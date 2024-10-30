import logging

from django.core.exceptions import ValidationError
from django.db import transaction

import requests

from openforms.forms.api.validators import FormIOComponentsValidator
from openforms.forms.models import Form, FormDefinition, FormStep

from .api_models import Field, FieldTypes
from .client import NoServiceConfigured, get_open_producten_client
from .models import ProductType

logger = logging.getLogger(__name__)


def _generate_configuration(fields: list[Field]) -> dict:
    components = [
        {
            "label": "Price Options",
            "type": "productPrice",
            "key": "productPrice",
            "validate": {"required": True},
        }
    ]

    for field in fields:

        if field.type not in (field_type.value for field_type in FieldTypes):
            raise ValidationError(f"Unknown field type {field.type}")

        component = {
            "type": field.type,
            "key": field.name,
            "label": field.name,
            "description": field.description,
        }

        if field.is_required:
            component["validate"] = {"required": True}

        if FieldTypes(field.type) == FieldTypes.SELECT:
            component["data"] = {
                "values": [
                    {"label": choice, "value": choice} for choice in field.choices
                ]
            }

        elif FieldTypes(field.type) in (FieldTypes.RADIO, FieldTypes.SELECT_BOXES):
            component["values"] = [
                {"label": choice, "value": choice} for choice in field.choices
            ]

        components.append(component)

    return {"components": components}


class FormGenerationException(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


@transaction.atomic()
def generate_product_form(product_type: ProductType):
    try:
        open_producten_client = get_open_producten_client()

        fields = open_producten_client.get_product_type_fields(product_type.uuid)
        configuration = _generate_configuration(fields)

        validator = FormIOComponentsValidator()
        validator(configuration)

        form_definition = FormDefinition.objects.create(
            name=f"{product_type.name} stap",
            name_en=f"{product_type.name} step",
            name_nl=f"{product_type.name} stap",
            configuration=configuration,
        )
        form = Form.objects.create(
            name=f"{product_type.name} formulier",
            name_en=f"{product_type.name} form",
            name_nl=f"{product_type.name} formulier",
            active=False,
            maintenance_mode=True,
            product=product_type,
        )
        FormStep.objects.create(form=form, form_definition=form_definition)

        open_producten_client.set_product_type_form_link(product_type.uuid, form)

    except NoServiceConfigured:
        raise FormGenerationException("No open producten service configured.")
    except requests.RequestException as exc:
        raise FormGenerationException(
            f"product type {product_type.name} request(s) to Open Producten failed."
        ) from exc
    except ValidationError as exc:
        logger.error(
            f"form generation for product type {product_type.name} failed on configuration validation",
            exc_info=exc,
        )
        raise FormGenerationException(
            f"generated configuration for product {product_type.name} is invalid."
        ) from exc
    except Exception as exc:
        logger.error("form generation failed", exc_info=exc)
        raise FormGenerationException(
            "Something went wrong while generating forms."
        ) from exc
