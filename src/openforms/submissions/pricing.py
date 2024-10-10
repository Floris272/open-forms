import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from json_logic import jsonLogic

if TYPE_CHECKING:
    from .models import Submission


logger = logging.getLogger(__name__)


def get_submission_price(submission: "Submission") -> Decimal:
    """
    Calculate the price for a given submission.

    If payment is required, the price logic rules are evaluated if present. If no
    pricing logic rules exist or there is no match, the linked product price is
    returned.

    :param submission: the :class:`openforms.submissions.models.Submission: instance
      to calculate the price for.
    :return: the calculated price.
    """
    assert (
        submission.form
    ), "Price cannot be calculated on a submission without the form relation set"
    assert submission.form.product, "Form must have a related product"
    assert (
        submission.form.product.price or submission.form.product.open_producten_price
    ), "get_submission_price' may only be called for forms that require payment"

    form = submission.form
    data = submission.data

    # test the rules one by one, if relevant
    price_rules = form.formpricelogic_set.all()
    for rule in price_rules:
        # logic does not match, no point in bothering
        if not jsonLogic(rule.json_logic_trigger, data):
            continue
        logger.debug(
            "Price for submission %s calculated using logic trigger %d: %r",
            submission.uuid,
            rule.id,
            rule.json_logic_trigger,
        )
        # first logic match wins
        # TODO: validate on API/backend/frontend that logic triggers must be unique for
        # a form
        return rule.price

    if form.product.open_producten_price:
        # method is called before form is completed at openforms.submissions.models.submission.Submission.payment_required

        def get_price_option_key():
            for step in form.formstep_set.all():
                for component in step.form_definition.configuration["components"]:
                    if component["type"] == "productPrice":
                        return component["key"]
            raise ValueError("form does not have a productPrice component")

        price_option_key = get_price_option_key()

        if not data.get(price_option_key):
            return Decimal("0")

        # should keep current price if already set.
        if submission.price:
            return submission.price

        logger.debug("Price for submission set by product price option")
        return form.product.open_producten_price.options.get(
            uuid=data[price_option_key]
        ).amount

    # no price rules or no match found -> use linked product
    logger.debug(
        "Falling back to product price for submission %s after trying %d price rules",
        submission.uuid,
        len(price_rules),
    )
    return form.product.price
