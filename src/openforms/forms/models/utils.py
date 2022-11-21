from dataclasses import dataclass
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase

from openforms.config.models import GlobalConfiguration


@dataclass
class literal_getter:
    """
    'Descriptor' to access a model field with a :class:`GlobalConfiguration` default.
    """

    model_field: str
    config_field: str
    language_code: Optional[str] = None

    def contribute_to_class(self, cls: ModelBase, name: str) -> None:
        # validate the existing fields were passed in - raises django.core.exceptions.FieldDoesNotExist
        assert cls._meta.get_field(self.model_field)
        assert GlobalConfiguration._meta.get_field(self.config_field)

        # generate the getter function & set it on the class
        def getter(instance: models.Model) -> str:
            model_field = self.model_field
            config_field = self.config_field
            if self.language_code:
                model_field = f"{self.model_field}_{self.language_code}"
                config_field = f"{self.config_field}_{self.language_code}"

            value = getattr(instance, model_field)
            if value:
                return value

            config = GlobalConfiguration.get_solo()
            return getattr(config, config_field)

        setattr(cls, name, getter)


def set_dynamic_literal_getters(
    literal_names: List, cls: ModelBase, config_field_prefix: str
) -> None:
    """
    Dynamically create literal getters for each available language
    """
    for literal in literal_names:
        for language_code, _label in settings.LANGUAGES:
            getter = literal_getter(
                literal,
                f"{config_field_prefix}_{literal}",
                language_code=language_code,
            )
            getter.contribute_to_class(cls, f"get_{literal}_{language_code}")
