import logging

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from openforms.contrib.open_producten.generate_form import (
    FormGenerationException,
    generate_product_form,
)
from openforms.products.models import Product

logger = logging.getLogger(__name__)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    actions = ["generate_form"]

    def generate_form(self, request, queryset):
        generated_product_names = []
        logger.info(generated_product_names)
        for product in queryset.filter(prices__isnull=False).distinct():
            try:
                generate_product_form(product)
                generated_product_names.append(product.name)
            except FormGenerationException as exc:
                self.message_user(
                    request=request, message=exc.message, level=messages.ERROR
                )

        self.message_user(
            request,
            _("{} form(s) generated {}").format(
                len(generated_product_names), " ".join(generated_product_names)
            ),
            messages.SUCCESS,
        )
