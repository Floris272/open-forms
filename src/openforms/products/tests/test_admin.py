import datetime
from unittest.mock import patch

from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.urls import reverse

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.contrib.open_producten.generate_form import FormGenerationException
from openforms.contrib.open_producten.tests.factories import PriceFactory
from openforms.products.tests.factories import ProductFactory


@override_settings(LANGUAGE_CODE="en")
class TestProductAdmin(TestCase):

    def setUp(self):
        user = SuperUserFactory.create()
        self.client.login(
            request=HttpRequest(), username=user.username, password="secret"
        )
        self.url = reverse("admin:products_product_changelist")

    @patch("openforms.products.admin.product.generate_product_form")
    def test_generate_form_action_with_product_that_has_price(
        self, mock_generate_product_form
    ):
        product = ProductFactory()
        PriceFactory.create(product_type=product, valid_from=datetime.date(2024, 1, 1))

        data = {"action": "generate_form", "_selected_action": [product.pk]}

        response = self.client.post(self.url, data, follow=True)

        mock_generate_product_form.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 form(s) generated")
        self.assertNotContains(response, "error")

        self.client.logout()

    @patch("openforms.products.admin.product.generate_product_form")
    def test_generate_form_action_with_product_that_has_no_price(
        self, mock_generate_product_form
    ):
        product = ProductFactory()
        data = {"action": "generate_form", "_selected_action": [product.pk]}

        response = self.client.post(self.url, data, follow=True)

        mock_generate_product_form.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 form(s) generated")
        self.assertNotContains(response, "error")

    @patch(
        "openforms.products.admin.product.generate_product_form",
        side_effect=FormGenerationException("test error"),
    )
    def test_generate_form_action_with_form_generation_exception(
        self, mock_generate_product_form
    ):
        product = ProductFactory()
        PriceFactory.create(product_type=product, valid_from=datetime.date(2024, 1, 1))

        data = {"action": "generate_form", "_selected_action": [product.pk]}

        response = self.client.post(self.url, data, follow=True)

        mock_generate_product_form.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 form(s) generated")
        self.assertContains(response, "error")
        self.assertContains(response, "Test error")

    @patch("openforms.products.admin.product.generate_product_form")
    def test_generate_form_action_with_multiple_products(
        self, mock_generate_product_form
    ):
        product_with_price = ProductFactory()
        PriceFactory.create(
            product_type=product_with_price, valid_from=datetime.date(2024, 1, 1)
        )

        product_without_price = ProductFactory()

        data = {
            "action": "generate_form",
            "_selected_action": [product_with_price.pk, product_without_price.pk],
        }

        response = self.client.post(self.url, data, follow=True)

        mock_generate_product_form.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 form(s) generated")
        self.assertNotContains(response, "error")
