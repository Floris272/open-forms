from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from zgw_consumers.api_models.base import Model


@dataclass
class PriceOption(Model):
    id: str
    amount: str
    description: str


@dataclass
class Price(Model):
    id: str
    valid_from: date
    options: list[PriceOption]


@dataclass
class ProductType(Model):
    id: str
    name: str
    current_price: Optional[Price]
    upl_name: str
    upl_uri: str


class FieldTypes(Enum):
    """Formio field types used in Open Forms."""

    BSN = "bsn"
    CHECKBOX = "checkbox"
    COSIGN = "Cosign"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    IBAN = "iban"
    LICENSE_PLATE = "licenseplate"
    MAP = "map"
    NUMBER = "number"
    PASSWORD = "password"
    PHONE_NUMBER = "phoneNumber"
    POSTCODE = "postcode"
    RADIO = "radio"
    SELECT = "select"
    SELECT_BOXES = "selectBoxes"
    SIGNATURE = "signature"
    TEXTFIELD = "textfield"
    TIME = "time"


@dataclass
class Field(Model):
    id: str
    name: str
    description: str
    type: FieldTypes
    is_required: bool
    choices: list[str]
