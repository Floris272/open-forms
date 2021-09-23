from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _

from timeline_logger.models import TimelineLog

from openforms.submissions.models import Submission


class TimelineLogProxyQueryset(models.QuerySet):
    def filter_event(self, event: str):
        return self.filter(extra_data__log_event=event)


class TimelineLogProxy(TimelineLog):
    objects = TimelineLogProxyQueryset.as_manager()

    class Meta:
        proxy = True
        verbose_name = _("timeline log entry")
        verbose_name_plural = _("timeline log entries")

    @property
    def fmt_lead(self) -> str:
        if self.is_submission:
            return f"[{self.fmt_time}] ({self.fmt_sub})"
        elif self.content_type_id:
            return (
                f"[{self.fmt_time}] ({self.content_type.name} {self.content_object.id})"
            )
        else:
            return f"[{self.fmt_time}]"

    @property
    def fmt_time(self) -> str:
        local_timestamp = timezone.localtime(self.timestamp)
        return local_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")

    @property
    def fmt_sub(self) -> str:
        if not self.is_submission:
            return ""
        return f"Submission {self.content_object.id}"

    @property
    def fmt_user(self) -> str:
        if self.user_id:
            return '{} "{}"'.format(gettext("User"), str(self.user))
        return gettext("Anonymous user")

    @property
    def fmt_form(self) -> str:
        if not self.is_submission:
            return ""
        return f'"{self.content_object.form}" (ID: {self.content_object.form_id})'

    @property
    def is_submission(self) -> bool:
        return bool(self.content_type == ContentType.objects.get_for_model(Submission))

    @property
    def fmt_plugin(self) -> str:
        if not self.extra_data:
            return _("(unknown)")
        plugin_id = self.extra_data.get("plugin_id", "")
        plugin_label = self.extra_data.get("plugin_label", "")
        if not any([plugin_id, plugin_label]):
            return ""
        return f'"{plugin_label}" ({plugin_id})'

    @property
    def fmt_fields(self) -> str:
        if not self.extra_data or "fields" not in self.extra_data:
            return _("(unknown)")
        return ", ".join(self.extra_data["fields"])

    @property
    def fmt_url(self) -> str:
        if not self.extra_data or "url" not in self.extra_data:
            return _("(unknown)")
        return self.extra_data["url"]

    @property
    def content_admin_url(self) -> str:
        if not (self.object_id and self.content_type_id):
            return ""

        ct = self.content_type
        return reverse(
            f"admin:{ct.app_label}_{ct.model}_change", args=(self.object_id,)
        )

    def content_admin_link(self) -> str:
        if not (url := self.content_admin_url):
            return ""

        return format_html('<a href="{u}">{t}</a>', u=url, t=str(self.content_object))

    content_admin_link.short_description = _("content object")

    def message(self) -> str:
        return self.get_message()

    message.short_description = _("message")
