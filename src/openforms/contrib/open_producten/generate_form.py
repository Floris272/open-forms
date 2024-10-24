from django.db import transaction

from ...forms.api.validators import FormIOComponentsValidator
from ...forms.models import Form, FormDefinition, FormStep
from .api_models import Field, FieldTypes
from .client import get_open_producten_client
from .models import ProductType


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
        component = {
            "type": field.type.value,
            "key": field.name,
            "label": field.name,
            "description": field.description,
        }

        if field.is_required:
            component["validate"] = {"required": True}

        if field.type == FieldTypes.SELECT:
            component["data"] = {
                "values": [
                    {"label": choice, "value": choice} for choice in field.choices
                ]
            }

        elif field.type in (FieldTypes.RADIO, FieldTypes.SELECT_BOXES):
            component["values"] = [
                {"label": choice, "value": choice} for choice in field.choices
            ]

        components.append(component)

    return {"components": components}


@transaction.atomic()
def generate_form(product_type: ProductType) -> Form:
    open_producten_client = get_open_producten_client()

    fields = open_producten_client.get_product_type_fields(product_type.uuid)
    configuration = _generate_configuration(fields)

    validator = FormIOComponentsValidator()
    validator(configuration)  # TODO does this work?

    form_definition = FormDefinition.objects.create(
        name=f"{product_type.name} form definition", configuration=configuration
    )
    form = Form.objects.create(
        name=f"{product_type.name} form",
        active=False,
        maintenance_mode=True,
        product=product_type,
    )
    FormStep.objects.create(form=form, form_definition=form_definition)

    return form
