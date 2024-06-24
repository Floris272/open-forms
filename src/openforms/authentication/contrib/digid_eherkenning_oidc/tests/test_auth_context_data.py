"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

import warnings

from django.test import override_settings
from django.urls import reverse

from django_webtest import DjangoTestApp

from openforms.authentication.tests.utils import AuthContextAssertMixin, URLsHelper
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import keycloak_login

from .base import (
    IntegrationTestsBase,
    mock_digid_config,
    mock_digid_machtigen_config,
    mock_eherkenning_bewindvoering_config,
    mock_eherkenning_config,
)


class PerformLoginMixin:
    app: DjangoTestApp
    extra_environ: dict

    def _login_and_start_form(self, plugin: str, *, username: str, password: str):
        host = f"http://{self.extra_environ['HTTP_HOST']}"
        form = FormFactory.create(authentication_backends=[plugin])
        url_helper = URLsHelper(form=form, host=host)
        start_url = url_helper.get_auth_start(plugin_id=plugin)
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username=username,
            password=password,
            host=host,
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_config()
    def test_record_auth_context(self):
        self._login_and_start_form(
            "digid_oidc", username="testuser", password="testuser"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_config()
    def test_record_auth_context(self):
        self._login_and_start_form(
            "eherkenning_oidc", username="testuser", password="testuser"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertNotIn("representee", auth_context)


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDMachtigenAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_machtigen_config()
    def test_record_auth_context(self):
        self._login_and_start_form(
            "digid_machtigen_oidc",
            username="digid-machtigen",
            password="digid-machtigen",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "999999999"},
        )
        # TODO: remove in Open Forms 3.0
        with self.subTest("legacy structure"):
            machtigen = submission.auth_info.machtigen
            self.assertEqual(machtigen, {"identifier_value": "999999999"})

    @mock_digid_machtigen_config(mandate_service_id_claim=["required-but-absent-claim"])
    def test_new_required_claims_are_backwards_compatible(self):
        """
        Test that the legacy configuration without additional claims still works.

        The extra authentication context (metadata) is required in the new flow, but
        this data was not extracted and/or provided before, so existing incomplete
        infrastructure should not break existing forms. At worst, we send non-compliant
        data to the registration backend/our own database, but that should not have
        runtime implications.
        """
        warnings.warn(
            "Legacy behaviour will be removed in Open Forms 3.0", DeprecationWarning
        )
        self._login_and_start_form(
            "digid_machtigen_oidc",
            username="digid-machtigen",
            password="digid-machtigen",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()
        # it is NOT valid according to the JSON schema (!) due to the missing service
        # ID claim
        self.assertEqual(auth_context["source"], "digid")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "999999999"},
        )
        # TODO: remove in Open Forms 3.0
        with self.subTest("legacy structure"):
            machtigen = submission.auth_info.machtigen
            self.assertEqual(machtigen, {"identifier_value": "999999999"})


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningBewindvoeringAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_bewindvoering_config()
    def test_record_auth_context(self):
        self._login_and_start_form(
            "eherkenning_bewindvoering_oidc",
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertEqual(
            auth_context["mandate"],
            {
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "81216fa4-80a1-4686-a8ac-5c8e5c030c93",
                    }
                ],
            },
        )

        # TODO: remove in Open Forms 3.0
        with self.subTest("legacy structure"):
            machtigen = submission.auth_info.machtigen
            self.assertEqual(machtigen, {"identifier_value": "12345678"})
