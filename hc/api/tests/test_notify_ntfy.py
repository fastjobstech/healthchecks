# coding: utf-8

from __future__ import annotations

import json
from datetime import timedelta as td
from unittest.mock import Mock, patch

from django.utils.timezone import now

from hc.api.models import Channel, Check, Notification, Ping
from hc.test import BaseTestCase


class NotifyNtfyTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.check = Check(project=self.project)
        self.check.name = "Foo"
        self.check.tags = "foo bar"
        self.check.n_pings = 123
        self.check.status = "down"
        self.check.last_ping = now() - td(minutes=61)
        self.check.save()

        self.ping = Ping(owner=self.check)
        self.ping.n = 1
        self.ping.remote_addr = "1.2.3.4"
        self.ping.save()

        self.channel = Channel(project=self.project)
        self.channel.kind = "ntfy"
        self.channel.value = json.dumps(
            {
                "url": "https://example.org",
                "topic": "foo",
                "priority": 5,
                "priority_up": 1,
            }
        )
        self.channel.save()
        self.channel.checks.add(self.check)

    @patch("hc.api.transports.curl.request")
    def test_it_works(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["title"], "Foo is DOWN")
        self.assertIn("Project: Alices Project", payload["message"])
        self.assertIn("Tags: foo, bar", payload["message"])
        self.assertIn("Period: 1 day", payload["message"])
        self.assertIn("Total Pings: 123", payload["message"])
        self.assertIn("Last Ping: Success, now", payload["message"])

        self.assertEqual(payload["actions"][0]["url"], self.check.cloaked_url())
        self.assertNotIn("All the other checks are up.", payload["message"])

    @patch("hc.api.transports.curl.request")
    def test_it_shows_schedule_and_tz(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        self.check.kind = "cron"
        self.check.tz = "Europe/Riga"
        self.check.save()
        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("Schedule: * * * * *", payload["message"])
        self.assertIn("Time Zone: Europe/Riga", payload["message"])

    @patch("hc.api.transports.curl.request")
    def test_it_shows_all_other_checks_up_note(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        other = Check(project=self.project)
        other.name = "Foobar"
        other.status = "up"
        other.last_ping = now() - td(minutes=61)
        other.save()

        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("All the other checks are up.", payload["message"])

    @patch("hc.api.transports.curl.request")
    def test_it_lists_other_down_checks(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        other = Check(project=self.project)
        other.name = "Foobar"
        other.status = "down"
        other.last_ping = now() - td(minutes=61)
        other.save()

        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("The following checks are also down", payload["message"])
        self.assertIn("Foobar", payload["message"])

    @patch("hc.api.transports.curl.request")
    def test_it_does_not_show_more_than_10_other_checks(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        for i in range(0, 11):
            other = Check(project=self.project)
            other.name = f"Foobar #{i}"
            other.status = "down"
            other.last_ping = now() - td(minutes=61)
            other.save()

        self.channel.notify(self.check)

        payload = mock_post.call_args.kwargs["json"]
        self.assertNotIn("Foobar", payload["message"])
        self.assertIn("11 other checks are also down.", payload["message"])

    @patch("hc.api.transports.curl.request")
    def test_it_uses_access_token(self, mock_post: Mock) -> None:
        mock_post.return_value.status_code = 200

        self.channel.value = json.dumps(
            {
                "url": "https://example.org",
                "topic": "foo",
                "priority": 5,
                "priority_up": 1,
                "token": "tk_test",
            }
        )
        self.channel.save()

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        headers = mock_post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer tk_test")
