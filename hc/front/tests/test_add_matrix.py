from __future__ import annotations

from unittest.mock import Mock, patch

from django.test.utils import override_settings

from hc.api.models import Channel
from hc.test import BaseTestCase


@override_settings(MATRIX_ACCESS_TOKEN="foo")
@override_settings(MATRIX_HOMESERVER="fake-homeserver")
class AddMatrixTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = f"/projects/{self.project.code}/add_matrix/"

    @override_settings(MATRIX_ACCESS_TOKEN="foo")
    def test_instructions_work(self) -> None:
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        self.assertContains(r, "Integration Settings", status_code=200)

    @patch("hc.front.forms.curl.post")
    def test_it_works(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"room_id": "fake-room-id"}

        form = {"alias": "!foo:example.org"}
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, form)
        self.assertRedirects(r, self.channels_url)

        c = Channel.objects.get()
        self.assertEqual(c.kind, "matrix")
        self.assertEqual(c.value, "fake-room-id")
        self.assertEqual(c.project, self.project)

    @override_settings(MATRIX_ACCESS_TOKEN=None)
    def test_it_requires_access_token(self) -> None:
        self.client.login(username="alice@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 404)

    @patch("hc.front.forms.curl.post")
    def test_it_handles_429(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 429

        form = {"alias": "!foo:example.org"}
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, form)

        self.assertContains(r, "Matrix server returned status code 429")
        self.assertFalse(Channel.objects.exists())

    @patch("hc.front.forms.curl.post")
    def test_it_handles_502(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 502

        form = {"alias": "!foo:example.org"}
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(self.url, form)

        self.assertContains(r, "Matrix server returned status code 502")
        self.assertFalse(Channel.objects.exists())

    def test_it_requires_rw_access(self) -> None:
        self.bobs_membership.role = "r"
        self.bobs_membership.save()

        self.client.login(username="bob@example.org", password="password")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)
