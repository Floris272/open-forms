# Generated by Django 3.2.21 on 2023-09-21 13:25

import django.db.models.deletion
from django.conf import settings
from django.core.cache import caches
from django.db import migrations, models

from zgw_consumers.constants import APITypes, AuthTypes


def get_common_prefix(values: list[str]) -> str:
    def _iter():
        for chars in zip(*values):
            # every char is identical
            if len(set(chars)) == 1:
                yield chars[0]
            else:
                return

    return "".join(_iter())


def set_kvk_service(apps, _):
    """
    Derive the "common" API root for KVK interaction.

    The zoeken/basisprofielen API's were historically separate services because they
    have their own OpenAPI specs and zgw_consumers requires api_root to be unique. Not
    doing this doesn't allow using zgw_consumers.Service.build_client (which needs the
    OAS).

    However, in the Great Refactor Of API Clients, we're moving away from
    zds-client/zgw-consumers for these clients, in favour of a more straight-forward
    requests-based approach. This allows us to properly clean up the configuration
    again.

    The API specs define the URL paths with the major version in the URL, e.g.
    ``/v1/basisprofielen/{kvkNummer}``, so our roots really need to be relative to that.
    """
    Service = apps.get_model("zgw_consumers", "Service")
    KVKConfig = apps.get_model("kvk", "KVKConfig")
    config = KVKConfig.objects.first()
    if config is None:
        return

    roots = []
    _existing = None  # to borrow the API credentials from the service

    if service := config._service:
        _existing = service
        roots.append(service.api_root)

    if service := config._profiles:
        if not _existing:
            _existing = service
        roots.append(service.api_root)

    # nothing was configured -> let the future `default` kick in
    if not roots:
        return

    # okay, now check what the common base is, as that will become the new API root.
    # We strip of the v1 suffix, as we'll add that ourselves in the clients.
    common_root = get_common_prefix(roots)
    if common_root.endswith("v1/"):
        common_root = common_root[:-3]
    elif common_root.endswith("v1"):
        common_root = common_root[:-2]

    service, _ = Service.objects.get_or_create(
        api_root=common_root,
        defaults={
            "label": "KVK API",
            "oas_url": common_root,  # expected to 404, but that's okay, we don't use it
            "type": APITypes.orc,
            "auth_type": _existing.auth_type if _existing else AuthTypes.api_key,
            "header_key": _existing.header_key if _existing else "apikey",
            # can't provide a default for this
            "header_value": _existing.header_value if _existing else "",
            "client_certificate": _existing.client_certificate if _existing else None,
            "server_certificate": _existing.server_certificate if _existing else None,
        },
    )
    config.service = service
    config.save()
    caches[settings.SOLO_CACHE].clear()


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0019_alter_service_uuid"),
        ("kvk", "0004_auto_20220203_1709"),
    ]

    operations = [
        migrations.AddField(
            model_name="kvkconfig",
            name="service",
            field=models.OneToOneField(
                help_text="Service for API interaction with the KVK.",
                limit_choices_to={"api_type": "orc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="KvK API",
            ),
        ),
        migrations.RunPython(set_kvk_service, migrations.RunPython.noop),
    ]
