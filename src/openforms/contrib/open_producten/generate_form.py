from django.db import transaction

from ...forms.api.validators import FormIOComponentsValidator
from ...forms.models import Form, FormDefinition, FormStep
from .models import FieldTypes, ProductType


def _generate_configuration(product_type: ProductType) -> dict:
    components = [
        {
            "label": "Price Options",
            "type": "productPrice",
            "key": "productPrice",
            "validate": {"required": True},
        }
    ]

    for field in product_type.fields.all():
        component = {
            "type": field.type,
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
    configuration = _generate_configuration(product_type)

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
