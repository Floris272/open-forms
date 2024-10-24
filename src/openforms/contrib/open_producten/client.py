import logging

import requests
from ape_pie import APIClient
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client

from openforms.contrib.open_producten.models import OpenProductenConfig

from .api_models import Field, ProductType

logger = logging.getLogger(__name__)


class OpenProductenClient(APIClient):
    def get_current_prices(self) -> list[ProductType]:
        try:
            response = self.get("producttypes/current-prices")
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "exception while fetching current prices from Open Producten",
                exc_info=exc,
            )
            raise exc

        data = response.json()
        product_types = factory(ProductType, data)

        return product_types

    def get_product_type_fields(self, product_type_uuid) -> list[Field]:
        try:
            response = self.get(f"producttypes/{product_type_uuid}/fields")
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "exception while making KVK basisprofiel request", exc_info=exc
            )
            raise exc

        data = response.json()
        fields = factory(Field, data)

        return fields


class NoServiceConfigured(RuntimeError):
    pass


def get_open_producten_client() -> OpenProductenClient:
    config = OpenProductenConfig.get_solo()
    if not (service := config.producten_service):
        raise NoServiceConfigured("No open producten service configured!")
    return build_client(service, client_factory=OpenProductenClient)
