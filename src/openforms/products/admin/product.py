from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from openforms.contrib.open_producten.generate_form import generate_form
from openforms.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    actions = ["generate_form"]

    def generate_form(self, request, queryset):
        for product in queryset:
            generate_form(product)

        self.message_user(
            request,
            _("{} forms generated").format(queryset.count()),
            messages.SUCCESS,
        )
