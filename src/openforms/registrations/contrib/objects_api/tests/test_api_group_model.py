from copy import copy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils.translation import gettext as _

from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIGroupConfig
from .factories import ObjectsAPIGroupConfigFactory

VCR_TEST_FILES = Path(__file__).parent / "files"


class ObjectsAPIGroupTests(TestCase):

    def test_can_save_without_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="",
            catalogue_rsin="",
        )

        self.assertIsNotNone(instance.pk)

    def test_can_save_with_catalogue_information(self):
        # checks that the check constraints are defined correctly
        instance = ObjectsAPIGroupConfigFactory.create(
            catalogue_domain="Test",
            catalogue_rsin="123456782",
        )

        self.assertIsNotNone(instance.pk)

    def test_cannot_save_with_partial_information(self):
        # checks that the check constraints are defined correctly
        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="Test", catalogue_rsin=""
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ObjectsAPIGroupConfigFactory.create(
                catalogue_domain="", catalogue_rsin="123456782"
            )

    def test_must_specify_catalogue_when_providing_iot_description(self):
        for field in (
            "iot_submission_report",
            "iot_submission_csv",
            "iot_attachment",
        ):
            with (
                self.subTest(field=field),
                transaction.atomic(),
                self.assertRaises(IntegrityError),
            ):
                ObjectsAPIGroupConfigFactory.create(
                    catalogue_domain="",
                    catalogue_rsin="",
                    **{field: "some-description"},
                )

    def test_normalize_documenttype_information(self):
        with self.subTest("no catalogue/document type anywhere"):
            api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build(
                catalogue_domain="",
                catalogue_rsin="",
                iot_submission_report="",
                iot_submission_csv="",
                iot_attachment="",
            )
            partial_opts = {
                "iot_submission_report": "",
                "iot_submission_csv": "",
                "iot_attachment": "",
            }

            api_group.apply_defaults_to(partial_opts)

            self.assertEqual(
                partial_opts,
                {
                    "catalogue": None,
                    "iot_submission_report": "",
                    "iot_submission_csv": "",
                    "iot_attachment": "",
                },
            )

        with self.subTest("default catalogue/document types on API group only"):
            api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build(
                catalogue_domain="TEST",
                catalogue_rsin="000000000",
                iot_submission_report="",
                iot_submission_csv="",
                iot_attachment="bijlage",
            )
            partial_opts = {
                "iot_submission_report": "",
                "iot_submission_csv": "",
                "iot_attachment": "",
            }

            api_group.apply_defaults_to(partial_opts)

            self.assertEqual(
                partial_opts,
                {
                    "catalogue": {
                        "domain": "TEST",
                        "rsin": "000000000",
                    },
                    "iot_submission_report": "",
                    "iot_submission_csv": "",
                    "iot_attachment": "bijlage",
                },
            )

        with self.subTest(
            "default catalogue/document types on API group, override in options"
        ):
            api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build(
                catalogue_domain="TEST",
                catalogue_rsin="000000000",
                iot_submission_report="some-default",
                iot_submission_csv="",
                iot_attachment="bijlage",
            )
            partial_opts = {
                "iot_submission_report": "",
                "iot_submission_csv": "",
                "iot_attachment": "other",
            }

            api_group.apply_defaults_to(partial_opts)

            self.assertEqual(
                partial_opts,
                {
                    "catalogue": {
                        "domain": "TEST",
                        "rsin": "000000000",
                    },
                    "iot_submission_report": "some-default",
                    "iot_submission_csv": "",
                    "iot_attachment": "other",
                },
            )

        with self.subTest("catalogue overriden, defaults set on API group"):
            api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build(
                catalogue_domain="TEST",
                catalogue_rsin="000000000",
                iot_submission_report="",
                iot_submission_csv="",
                iot_attachment="bijlage",
            )
            partial_opts = {
                "iot_submission_report": "",
                "iot_submission_csv": "",
                "iot_attachment": "",
                "catalogue": {
                    "domain": "OTHER",
                    "rsin": "000000000",
                },
            }

            api_group.apply_defaults_to(partial_opts)

            self.assertEqual(
                partial_opts,
                {
                    "catalogue": {
                        "domain": "OTHER",
                        "rsin": "000000000",
                    },
                    "iot_submission_report": "",
                    "iot_submission_csv": "",
                    "iot_attachment": "",
                },
            )

        with self.subTest("catalogue and doctype overriden, defaults set on API group"):
            api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build(
                catalogue_domain="TEST",
                catalogue_rsin="000000000",
                iot_submission_report="some-default",
                iot_submission_csv="",
                iot_attachment="bijlage",
            )
            partial_opts = {
                "iot_submission_report": "",
                "iot_submission_csv": "",
                "iot_attachment": "attachment",
                "catalogue": {
                    "domain": "OTHER",
                    "rsin": "000000000",
                },
            }

            api_group.apply_defaults_to(partial_opts)

            self.assertEqual(
                partial_opts,
                {
                    "catalogue": {
                        "domain": "OTHER",
                        "rsin": "000000000",
                    },
                    "iot_submission_report": "",
                    "iot_submission_csv": "",
                    "iot_attachment": "attachment",
                },
            )


class ObjectsAPIGroupValidationTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = VCR_TEST_FILES

    def test_validate_catalogue_exists(self):
        # validates against the fixtures in docker/open-zaak
        config = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="Nope",  # does not exist in fixtures
            catalogue_rsin="000000000",
        )

        with self.subTest("invalid catalogue"):
            with self.assertRaisesMessage(
                ValidationError,
                "The specified catalogue does not exist. Maybe you made a typo in the "
                "domain or RSIN?",
            ):
                config.clean()

        with self.subTest("valid catalogue"):
            config.catalogue_domain = "TEST"  # exists in the fixture
            try:
                config.clean()
            except ValidationError as exc:
                raise self.failureException(
                    "Catalogue exists and should vlaidate"
                ) from exc

    def test_validate_iot_urls_within_catalogue(self):
        config = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="OTHER",
            catalogue_rsin="000000000",
        )
        # it exists, just under a different catalogue
        invalid_url = (
            f"{config.catalogi_service.api_root}informatieobjecttypen/"
            "7a474713-0833-402a-8441-e467c08ac55b"
        )
        for field in (
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        ):
            with self.subTest(field=field):
                _config = copy(config)
                setattr(_config, field, invalid_url)

                with self.assertRaisesMessage(
                    ValidationError,
                    "The document type URL is not in the specified catalogue.",
                ) as exc_context:
                    _config.clean()

                self.assertEqual(list(exc_context.exception.error_dict.keys()), [field])

    def test_validate_iot_descriptions_within_catalogue(self):
        iot_in_test = "PDF Informatieobjecttype"
        iot_in_other = "Attachment Informatieobjecttype other catalog"
        config = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )

        for field in (
            "iot_submission_report",
            "iot_submission_csv",
            "iot_attachment",
        ):

            err = _("No document type with description {description} found.").format(
                description=iot_in_other
            )

            with (
                self.subTest(field=field, valid=False),
                self.assertRaisesMessage(ValidationError, err) as exc_context,
            ):
                invalid_config = copy(config)
                setattr(invalid_config, field, iot_in_other)

                invalid_config.clean()

            self.assertEqual(list(exc_context.exception.error_dict.keys()), [field])

            with self.subTest(field=field, valid=True):
                valid_config = copy(config)
                setattr(valid_config, field, iot_in_test)

                try:
                    valid_config.clean()
                except ValidationError as exc:
                    raise self.failureException(
                        "Configuration is supposed to be valid"
                    ) from exc
