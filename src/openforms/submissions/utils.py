import html
import logging
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import ObjectDoesNotExist
from django.template import Context, Template

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import send_mail_html, strip_tags_plus
from openforms.logging import logevent

from ..forms.constants import ConfirmationEmailOptions
from .constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from .models import Submission, TemporaryFileUpload

logger = logging.getLogger(__name__)


def append_to_session_list(session: SessionBase, session_key: str, value: Any) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value not in active:
        active.append(value)
        session[session_key] = active


def remove_from_session_list(
    session: SessionBase, session_key: str, value: Any
) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value in active:
        active.remove(value)
        session[session_key] = active


def add_submmission_to_session(submission: Submission, session: SessionBase) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    append_to_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def remove_submission_from_session(
    submission: Submission, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def add_upload_to_session(upload: TemporaryFileUpload, session: SessionBase) -> None:
    """
    Store the upload UUID in the request session for authorization checks.
    """
    append_to_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_upload_from_session(
    upload: TemporaryFileUpload, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_submission_uploads_from_session(
    submission: Submission, session: SessionBase
) -> None:
    for attachment in submission.get_attachments().filter(temporary_file__isnull=False):
        remove_upload_from_session(attachment.temporary_file, session)


def send_confirmation_email(submission: Submission):
    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        logevent.confirmation_email_skip(submission)
        return

    if (
        submission.form.confirmation_email_option
        == ConfirmationEmailOptions.form_specific_email
    ):
        try:
            email_template = submission.form.confirmation_email_template
            subject = email_template.subject
            html_content = email_template.render(submission)
            text_content = email_template.render(submission, {"rendering_text": True})
        except (AttributeError, ObjectDoesNotExist):
            logger.warning(
                "No form specific confirmation email template for submission %d, "
                "skipping the confirmation e-mail.",
                submission.id,
            )
            logevent.confirmation_email_skip(submission)
            return
    elif (
        submission.form.confirmation_email_option
        == ConfirmationEmailOptions.global_email
    ):
        config = GlobalConfiguration.get_solo()
        subject = Template(config.confirmation_email_subject).render(
            Context({"form_name": submission.form.name})
        )
        html_content = config.render_confirmation_email_content(submission)
        text_content = config.render_confirmation_email_content(
            submission, {"rendering_text": True}
        )
    else:
        logger.debug(
            "Form is not configured to send an email for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        logevent.confirmation_email_skip(submission)
        return

    # post process since the mail template has html markup and django escaped entities
    text_content = strip_tags_plus(text_content)
    text_content = html.unescape(text_content)

    send_mail_html(
        subject,
        html_content,
        settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
        to_emails,
        fail_silently=False,
        text_message=text_content,
    )

    submission.confirmation_email_sent = True
    submission.save(update_fields=("confirmation_email_sent",))

    logevent.confirmation_email_success(submission)
