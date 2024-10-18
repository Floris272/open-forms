import factory.fuzzy

from openforms.products.tests.factories import ProductFactory

from ..models import Field, Price, PriceOption


class PriceFactory(factory.django.DjangoModelFactory):
    uuid = factory.Faker("uuid4")
    valid_from = factory.Faker("date")
    product_type = factory.SubFactory(ProductFactory)

    class Meta:
        model = Price


class PriceOptionFactory(factory.django.DjangoModelFactory):
    uuid = factory.Faker("uuid4")
    description = factory.Faker("sentence")
    amount = factory.fuzzy.FuzzyDecimal(1, 10)
    price = factory.SubFactory(PriceFactory)

    class Meta:
        model = PriceOption


class FieldFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"field {n}")
    description = factory.Faker("sentence")
    product_type = factory.SubFactory(ProductFactory)

    class Meta:
        model = Field
