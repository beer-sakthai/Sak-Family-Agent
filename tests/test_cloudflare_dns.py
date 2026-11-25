"""Tests for Cloudflare DNS and Nameserver management automation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from infra.cloudflare.dns_manager import (
    create_nameserver_set,
    upsert_dns_record,
)


class TestCloudflareDNSManager:
    def test_validation_errors(self):
        with pytest.raises(ValueError, match="account_id is required"):
            create_nameserver_set(
                account_id="", name="prod", nameservers=[{"name": "ns1.example.com"}]
            )

        with pytest.raises(ValueError, match="name is required"):
            create_nameserver_set(
                account_id="acc1", name="", nameservers=[{"name": "ns1.example.com"}]
            )

        with pytest.raises(ValueError, match="nameservers list cannot be empty"):
            create_nameserver_set(account_id="acc1", name="prod", nameservers=[])

        with pytest.raises(ValueError, match="zone_id is required"):
            upsert_dns_record(zone_id="", record_type="A", name="sub", content="1.2.3.4")

    def test_create_nameserver_set_fallback(self):
        res = create_nameserver_set(
            account_id="023e105f4ecef8ad9ca31a8372d0c353",
            name="Production nameservers",
            nameservers=[{"name": "ns1.example.com"}],
        )
        assert res["account_id"] == "023e105f4ecef8ad9ca31a8372d0c353"
        assert res["name"] == "Production nameservers"
        assert res["status"] == "active"

    def test_create_nameserver_set_mocked_sdk(self):
        mock_client = MagicMock()
        mock_client.dns.settings.account.nameserver_sets.create.return_value = {
            "id": "ns_custom_id",
            "name": "Custom NS",
            "nameservers": [{"name": "ns1.example.com"}],
        }

        res = create_nameserver_set(
            account_id="acc_123",
            name="Custom NS",
            nameservers=[{"name": "ns1.example.com"}],
            client=mock_client,
        )
        assert res["id"] == "ns_custom_id"
        mock_client.dns.settings.account.nameserver_sets.create.assert_called_once_with(
            account_id="acc_123",
            name="Custom NS",
            nameservers=[{"name": "ns1.example.com"}],
        )

    def test_upsert_dns_record_mocked_sdk(self):
        mock_client = MagicMock()
        mock_client.dns.records.create.return_value = {
            "id": "rec_999",
            "name": "api.example.com",
            "content": "1.2.3.4",
        }

        res = upsert_dns_record(
            zone_id="zone_abc",
            record_type="A",
            name="api.example.com",
            content="1.2.3.4",
            client=mock_client,
        )
        assert res["id"] == "rec_999"
        mock_client.dns.records.create.assert_called_once_with(
            zone_id="zone_abc",
            type="A",
            name="api.example.com",
            content="1.2.3.4",
            ttl=1,
            proxied=False,
        )
