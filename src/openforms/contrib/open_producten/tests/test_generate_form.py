from datetime import date
from uuid import uuid4

from django.test import TestCase

from openforms.forms.models import Form, FormDefinition, FormStep
from openforms.products.tests.factories import ProductFactory

from ..generate_form import _generate_configuration, generate_form
from ..models import FieldTypes
from .factories import FieldFactory, PriceOptionFactory


class TestFormGeneration(TestCase):

    def setUp(self):
        self.product = ProductFactory.create()

        PriceOptionFactory.create(
            price__valid_from=date(2024, 1, 1),
            price__product_type=self.product,
        )

    def test_generate_configuration_with_textfield(self):
        field = FieldFactory.create(
            uuid=uuid4(), product_type=self.product, type=FieldTypes.TEXTFIELD
        )

        configuration = _generate_configuration(self.product)

        self.assertEqual(
            configuration,
            {
                "components": [
                    {
                        "label": "Price Options",
                        "type": "productPrice",
                        "key": "productPrice",
                        "validate": {"required": True},
                    },
                    {
                        "label": field.name,
                        "type": field.type,
                        "key": field.name,
                        "description": field.description,
                    },
                ]
            },
        )

    def test_generate_configuration_with_required_field(self):
        field = FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.TEXTFIELD,
            is_required=True,
        )

        configuration = _generate_configuration(self.product)

        self.assertEqual(
            configuration,
            {
                "components": [
                    {
                        "label": "Price Options",
                        "type": "productPrice",
                        "key": "productPrice",
                        "validate": {"required": True},
                    },
                    {
                        "label": field.name,
                        "type": field.type,
                        "key": field.name,
                        "description": field.description,
                        "validate": {"required": True},
                    },
                ]
            },
        )

    def test_generate_configuration_with_select(self):
        field = FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.SELECT,
            choices=["a", "b"],
        )
        configuration = _generate_configuration(self.product)

        self.assertEqual(
            configuration,
            {
                "components": [
                    {
                        "label": "Price Options",
                        "type": "productPrice",
                        "key": "productPrice",
                        "validate": {"required": True},
                    },
                    {
                        "label": field.name,
                        "type": field.type,
                        "key": field.name,
                        "description": field.description,
                        "data": {
                            "values": [
                                {"label": choice, "value": choice}
                                for choice in field.choices
                            ]
                        },
                    },
                ]
            },
        )

    def test_generate_configuration_with_radio(self):
        field = FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.RADIO,
            choices=["a", "b"],
        )
        configuration = _generate_configuration(self.product)

        self.assertEqual(
            configuration,
            {
                "components": [
                    {
                        "label": "Price Options",
                        "type": "productPrice",
                        "key": "productPrice",
                        "validate": {"required": True},
                    },
                    {
                        "label": field.name,
                        "type": field.type,
                        "key": field.name,
                        "description": field.description,
                        "values": [
                            {"label": choice, "value": choice}
                            for choice in field.choices
                        ],
                    },
                ]
            },
        )

    def test_generate_form(self):
        FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.TEXTFIELD,
            is_required=True,
            name="name",
            description="name textfield",
        )

        FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.DATE,
            name="date",
            description="datefield",
        )

        FieldFactory.create(
            uuid=uuid4(),
            product_type=self.product,
            type=FieldTypes.SELECT_BOXES,
            name="select boxes",
            description="select boxes",
            choices=["a", "b"],
        )

        generate_form(self.product)

        self.assertEqual(Form.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 1)
        self.assertEqual(FormDefinition.objects.count(), 1)

        form = Form.objects.first()
        definition = FormDefinition.objects.first()

        self.assertEqual(form.product, self.product)
        self.assertEqual(form.active, False)
        self.assertEqual(form.maintenance_mode, True)

        self.maxDiff = None

        self.assertEqual(
            definition.configuration,
            {
                "components": [
                    {
                        "label": "Price Options",
                        "type": "productPrice",
                        "key": "productPrice",
                        "validate": {"required": True},
                    },
                    {
                        "label": "name",
                        "type": "textfield",
                        "key": "name",
                        "description": "name textfield",
                        "validate": {"required": True},
                    },
                    {
                        "label": "date",
                        "type": "date",
                        "key": "date",
                        "description": "datefield",
                    },
                    {
                        "label": "select boxes",
                        "type": "selectBoxes",
                        "key": "select boxes",
                        "description": "select boxes",
                        "values": [
                            {"label": "a", "value": "a"},
                            {"label": "b", "value": "b"},
                        ],
                    },
                ]
            },
        )
