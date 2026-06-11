"""Anonymous welcome modal fields and dataset field config flags."""

import json
import uuid

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from datasets.models import (
    DEFAULT_ANONYMOUS_NAME_FIELD_LABEL,
    DEFAULT_ANONYMOUS_WELCOME_MESSAGE,
    DEFAULT_ANONYMOUS_WELCOME_TITLE,
    DEFAULT_DATA_INPUT_ADD_POINT_LABEL,
    DEFAULT_DATA_INPUT_MY_LOCATION_LABEL,
    DataSet,
    DatasetField,
    VirtualContributor,
)
from datasets.views.dataset_views import normalize_welcome_field_submission


class NormalizeWelcomeSubmissionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="o", password="p")
        self.dataset = DataSet.objects.create(name="D", owner=self.owner)
        self.field = DatasetField.objects.create(
            dataset=self.dataset,
            field_name="note",
            label="Note",
            field_type="text",
            enabled=True,
            anonymous_welcome=True,
        )

    def test_accepts_whitelisted_key(self):
        out = normalize_welcome_field_submission(self.dataset, {"note": "hello"})
        self.assertEqual(out, {"note": "hello"})

    def test_drops_unknown_keys(self):
        out = normalize_welcome_field_submission(self.dataset, {"note": "x", "other": "y"})
        self.assertEqual(out, {"note": "x"})

    def test_required_missing_raises(self):
        self.field.required = True
        self.field.save(update_fields=["required"])
        with self.assertRaises(ValueError):
            normalize_welcome_field_submission(self.dataset, {})


class RegisterVirtualUserWelcomeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="o", password="p")
        self.dataset = DataSet.objects.create(
            name="D",
            owner=self.owner,
            allow_anonymous_data_input=True,
        )
        self.dataset.ensure_anonymous_access_token()
        self.dataset.refresh_from_db()
        DatasetField.objects.create(
            dataset=self.dataset,
            field_name="org",
            label="Org",
            field_type="text",
            enabled=True,
            anonymous_welcome=True,
        )
        self.client = Client()

    def _session(self):
        s = self.client.session
        s[f"anonymous_token_{self.dataset.id}"] = self.dataset.anonymous_access_token
        s.save()

    def test_stores_welcome_values(self):
        self._session()
        u = str(uuid.uuid4())
        url = reverse("register_virtual_user", args=[self.dataset.id])
        r = self.client.post(
            url,
            data=json.dumps(
                {"uuid": u, "display_name": "Tester", "welcome_fields": {"org": "ACME"}}
            ),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))
        vc = VirtualContributor.objects.get(dataset=self.dataset, uuid=u)
        self.assertEqual(vc.welcome_field_values.get("org"), "ACME")

    def test_rejects_value_for_non_welcome_field(self):
        DatasetField.objects.create(
            dataset=self.dataset,
            field_name="hidden",
            label="Hidden",
            field_type="text",
            enabled=True,
            anonymous_welcome=False,
        )
        self._session()
        u = str(uuid.uuid4())
        url = reverse("register_virtual_user", args=[self.dataset.id])
        r = self.client.post(
            url,
            data=json.dumps(
                {
                    "uuid": u,
                    "display_name": "",
                    "welcome_fields": {"org": "OK", "hidden": "nope"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        vc = VirtualContributor.objects.get(dataset=self.dataset, uuid=u)
        self.assertEqual(vc.welcome_field_values.get("org"), "OK")
        self.assertNotIn("hidden", vc.welcome_field_values)


class DatasetDetailAnonymousWelcomeColumnTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="o", password="p")
        self.dataset = DataSet.objects.create(
            name="D",
            owner=self.owner,
            allow_anonymous_data_input=True,
        )
        self.field = DatasetField.objects.create(
            dataset=self.dataset,
            field_name="x",
            label="X",
            field_type="text",
            enabled=True,
            order=0,
        )
        self.client = Client()
        self.client.force_login(self.owner)

    def test_update_fields_sets_anonymous_welcome(self):
        url = reverse("dataset_detail", args=[self.dataset.id])
        r = self.client.post(
            url,
            {
                "action": "update_fields",
                f"field_{self.field.id}_order": "0",
                f"field_{self.field.id}_enabled": "on",
                f"field_{self.field.id}_anonymous_welcome": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.field.refresh_from_db()
        self.assertTrue(self.field.anonymous_welcome)

    def test_disables_anonymous_welcome_when_anon_input_off(self):
        self.dataset.allow_anonymous_data_input = False
        self.dataset.save(update_fields=["allow_anonymous_data_input"])
        self.field.anonymous_welcome = True
        self.field.save(update_fields=["anonymous_welcome"])
        url = reverse("dataset_detail", args=[self.dataset.id])
        self.client.post(
            url,
            {
                "action": "update_fields",
                f"field_{self.field.id}_order": "0",
                f"field_{self.field.id}_enabled": "on",
            },
        )
        self.field.refresh_from_db()
        self.assertFalse(self.field.anonymous_welcome)


class AnonymousWelcomeMessageTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="o", password="p")
        self.dataset = DataSet.objects.create(
            name="WelcomeMsg",
            owner=self.owner,
            allow_anonymous_data_input=True,
        )
        self.dataset.ensure_anonymous_access_token()
        self.dataset.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.owner)

    def _post_settings(self, **extra):
        data = {
            "name": self.dataset.name,
            "description": self.dataset.description or "",
            "allow_anonymous_data_input": "on",
            "data_input_show_street_view": "on",
        }
        data.update(extra)
        return self.client.post(
            reverse("dataset_settings", args=[self.dataset.id]),
            data,
        )

    def test_settings_page_includes_welcome_message_field(self):
        response = self.client.get(reverse("dataset_settings", args=[self.dataset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="anonymous_welcome_message"')
        self.assertContains(response, "Anonymous welcome message")

    def test_settings_post_saves_custom_message(self):
        custom = "Please contribute observations for this survey."
        response = self._post_settings(anonymous_welcome_message=custom)
        self.assertEqual(response.status_code, 302)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.anonymous_welcome_message, custom)

    def test_get_anonymous_welcome_message_default_when_blank(self):
        self.assertEqual(self.dataset.get_anonymous_welcome_message(), DEFAULT_ANONYMOUS_WELCOME_MESSAGE)

    def test_anonymous_data_input_renders_custom_message(self):
        custom = "Custom intro for anonymous users."
        self.dataset.anonymous_welcome_message = custom
        self.dataset.save(update_fields=["anonymous_welcome_message"])
        url = reverse(
            "dataset_data_input_anonymous",
            args=[self.dataset.id, self.dataset.anonymous_access_token],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, custom)

    def test_anonymous_data_input_renders_default_when_blank(self):
        url = reverse(
            "dataset_data_input_anonymous",
            args=[self.dataset.id, self.dataset.anonymous_access_token],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, DEFAULT_ANONYMOUS_WELCOME_MESSAGE)


class DataInputLabelSettingsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="labels", password="p")
        self.dataset = DataSet.objects.create(
            name="Labels DS",
            owner=self.owner,
            allow_anonymous_data_input=True,
        )
        self.dataset.ensure_anonymous_access_token()
        self.dataset.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.owner)

    def _post_settings(self, **extra):
        data = {
            "name": self.dataset.name,
            "description": self.dataset.description or "",
            "allow_anonymous_data_input": "on",
            "data_input_show_street_view": "on",
        }
        data.update(extra)
        return self.client.post(
            reverse("dataset_settings", args=[self.dataset.id]),
            data,
        )

    def test_settings_page_includes_label_fields(self):
        response = self.client.get(reverse("dataset_settings", args=[self.dataset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="data_input_add_point_label"')
        self.assertContains(response, 'name="data_input_my_location_label"')
        self.assertContains(response, 'name="anonymous_welcome_title"')
        self.assertContains(response, 'name="anonymous_name_field_label"')

    def test_settings_post_saves_custom_labels(self):
        response = self._post_settings(
            data_input_add_point_label="Punkt hinzufügen",
            data_input_my_location_label="Mein Standort",
            anonymous_welcome_title="Willkommen",
            anonymous_name_field_label="Ihr Name (optional)",
        )
        self.assertEqual(response.status_code, 302)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.data_input_add_point_label, "Punkt hinzufügen")
        self.assertEqual(self.dataset.data_input_my_location_label, "Mein Standort")
        self.assertEqual(self.dataset.anonymous_welcome_title, "Willkommen")
        self.assertEqual(self.dataset.anonymous_name_field_label, "Ihr Name (optional)")

    def test_getters_return_defaults_when_blank(self):
        self.assertEqual(
            self.dataset.get_data_input_add_point_label(),
            DEFAULT_DATA_INPUT_ADD_POINT_LABEL,
        )
        self.assertEqual(
            self.dataset.get_data_input_my_location_label(),
            DEFAULT_DATA_INPUT_MY_LOCATION_LABEL,
        )
        self.assertEqual(
            self.dataset.get_anonymous_welcome_title(),
            DEFAULT_ANONYMOUS_WELCOME_TITLE,
        )
        self.assertEqual(
            self.dataset.get_anonymous_name_field_label(),
            DEFAULT_ANONYMOUS_NAME_FIELD_LABEL,
        )

    def test_data_input_renders_custom_map_button_labels(self):
        self.dataset.data_input_add_point_label = "Add spot"
        self.dataset.data_input_my_location_label = "Where am I"
        self.dataset.save(update_fields=[
            "data_input_add_point_label",
            "data_input_my_location_label",
        ])
        response = self.client.get(reverse("dataset_data_input", args=[self.dataset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add spot")
        self.assertContains(response, "Where am I")
        self.assertContains(response, 'window.dataInputAddPointLabel = "Add spot"')

    def test_anonymous_data_input_renders_custom_welcome_labels(self):
        self.dataset.anonymous_welcome_title = "Hello there"
        self.dataset.anonymous_name_field_label = "Display name"
        self.dataset.save(update_fields=[
            "anonymous_welcome_title",
            "anonymous_name_field_label",
        ])
        url = reverse(
            "dataset_data_input_anonymous",
            args=[self.dataset.id, self.dataset.anonymous_access_token],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello there")
        self.assertContains(response, "Display name")


class ResetAnonymousVirtualUserTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="o", password="p")
        self.dataset = DataSet.objects.create(
            name="Reset",
            owner=self.owner,
            allow_anonymous_data_input=True,
        )
        self.dataset.ensure_anonymous_access_token()
        self.dataset.refresh_from_db()
        self.client = Client()

    def _session(self):
        s = self.client.session
        s[f"anonymous_token_{self.dataset.id}"] = self.dataset.anonymous_access_token
        s.save()

    def test_post_clears_session_and_redirects_with_flag(self):
        self._session()
        u = str(uuid.uuid4())
        reg = reverse("register_virtual_user", args=[self.dataset.id])
        r = self.client.post(
            reg,
            data=json.dumps({"uuid": u, "display_name": "Someone"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)

        sess = self.client.session
        self.assertEqual(sess.get(f"virtual_contributor_uuid_{self.dataset.id}"), u)

        rst = reverse("reset_anonymous_virtual_user", args=[self.dataset.id])
        r2 = self.client.post(rst)
        self.assertEqual(r2.status_code, 302)
        self.assertIn("anonymous_session_reset=1", r2["Location"])

        sess = self.client.session
        self.assertIsNone(sess.get(f"virtual_contributor_uuid_{self.dataset.id}"))

    def test_forbidden_when_not_in_anonymous_session(self):
        rst = reverse("reset_anonymous_virtual_user", args=[self.dataset.id])
        self.assertEqual(self.client.post(rst).status_code, 403)

    def test_get_not_allowed(self):
        self._session()
        rst = reverse("reset_anonymous_virtual_user", args=[self.dataset.id])
        self.assertEqual(self.client.get(rst).status_code, 405)
