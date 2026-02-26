"""
pytest suite for kafka_producer.py

Mirrors the 4 JS describe blocks from kafka-producer.test.js:
  - Missing config       → TestMissingConfig
  - Happy path           → TestHappyPath
  - Kafka client config  → TestProducerConfig / TestProducerConfigViaEnv
  - Error handling       → TestErrorHandling

Run from the project root:  pytest hooks/test_kafka_producer.py -v

Mocking strategy
----------------
confluent_kafka may not be installed in the dev environment; it's only needed
at hook runtime. We inject a fake module via patch.dict(sys.modules, ...) so
the deferred `from confluent_kafka import Producer` inside send_event picks up
our mock — no real broker required.
"""

from __future__ import annotations

import importlib
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KAFKA_ENV = {
    "FULCRUM_KAFKA_BROKERS": "broker1:9092,broker2:9092",
    "FULCRUM_KAFKA_TOPIC": "fulcrum-metrics",
}

FIXED_FIELDS = dict(
    event_type="workflow.session.started",
    session_id="abc-123",
    project="checkout-service",
    plugin_version="1.2.0",
)

_KAFKA_VARS = {
    "FULCRUM_KAFKA_BROKERS",
    "FULCRUM_KAFKA_TOPIC",
    "FULCRUM_KAFKA_CLIENT_ID",
    "FULCRUM_KAFKA_SSL",
    "FULCRUM_KAFKA_SASL_USERNAME",
    "FULCRUM_KAFKA_SASL_PASSWORD",
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove all FULCRUM_KAFKA_* vars before each test."""
    for key in _KAFKA_VARS:
        monkeypatch.delenv(key, raising=False)


def _set_kafka_env(monkeypatch, **overrides):
    for k, v in {**KAFKA_ENV, **overrides}.items():
        monkeypatch.setenv(k, v)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_mock_producer(*, produce_error=None, flush_error=None):
    """Return a mock Producer instance with controllable failure points."""
    mock_instance = MagicMock()
    if produce_error:
        mock_instance.produce.side_effect = produce_error
    if flush_error:
        mock_instance.flush.side_effect = flush_error
    return mock_instance


def _make_confluent_kafka_mock(producer_instance):
    """Return a fake confluent_kafka module whose Producer returns producer_instance."""
    mock_ck = MagicMock()
    mock_ck.Producer.return_value = producer_instance
    return mock_ck


def _reload_kp():
    """Reload kafka_producer so it picks up any sys.modules patch."""
    import kafka_producer as kp
    importlib.reload(kp)
    return kp


# ---------------------------------------------------------------------------
# TestMissingConfig
# ---------------------------------------------------------------------------


class TestMissingConfig:
    """send_event must exit early and never instantiate Producer when config is missing."""

    def test_skips_when_brokers_not_set(self, monkeypatch):
        monkeypatch.setenv("FULCRUM_KAFKA_TOPIC", "fulcrum-metrics")
        mock_ck = MagicMock()

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_ck.Producer.assert_not_called()

    def test_skips_when_topic_not_set(self, monkeypatch):
        monkeypatch.setenv("FULCRUM_KAFKA_BROKERS", "broker1:9092")
        mock_ck = MagicMock()

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_ck.Producer.assert_not_called()

    def test_skips_when_both_required_vars_absent(self):
        mock_ck = MagicMock()

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_ck.Producer.assert_not_called()


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_payload_contains_all_fixed_fields(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_instance.produce.assert_called_once()
        _, kwargs = mock_instance.produce.call_args
        payload = json.loads(kwargs["value"])

        assert payload["event_type"] == FIXED_FIELDS["event_type"]
        assert payload["session_id"] == FIXED_FIELDS["session_id"]
        assert payload["project"] == FIXED_FIELDS["project"]
        assert payload["plugin_version"] == FIXED_FIELDS["plugin_version"]
        assert "timestamp" in payload

    def test_metadata_field_present_in_payload(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()
        metadata = {"outcome": "branch_finished", "commits_count": 3}

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS, metadata=metadata)

        _, kwargs = mock_instance.produce.call_args
        payload = json.loads(kwargs["value"])
        assert payload["metadata"] == metadata

    def test_key_is_session_id(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        _, kwargs = mock_instance.produce.call_args
        assert kwargs["key"] == FIXED_FIELDS["session_id"].encode()

    def test_sends_to_topic_from_env(self, monkeypatch):
        _set_kafka_env(monkeypatch, FULCRUM_KAFKA_TOPIC="my-custom-topic")
        mock_instance = _make_mock_producer()

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        _, kwargs = mock_instance.produce.call_args
        assert kwargs["topic"] == "my-custom-topic"

    def test_flush_called_after_produce(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_instance.flush.assert_called_once()


# ---------------------------------------------------------------------------
# TestProducerConfig  — _build_producer_config directly
# ---------------------------------------------------------------------------


class TestProducerConfig:
    @pytest.fixture(autouse=True)
    def _import(self):
        import kafka_producer as kp
        importlib.reload(kp)
        self._build = kp._build_producer_config

    def test_default_security_protocol_is_plaintext(self):
        cfg = self._build("b:9092", "cid", False, None, None)
        assert cfg["security.protocol"] == "PLAINTEXT"

    def test_ssl_only_gives_ssl_protocol(self):
        cfg = self._build("b:9092", "cid", True, None, None)
        assert cfg["security.protocol"] == "SSL"

    def test_sasl_only_gives_sasl_plaintext(self):
        cfg = self._build("b:9092", "cid", False, "user", "pass")
        assert cfg["security.protocol"] == "SASL_PLAINTEXT"

    def test_ssl_and_sasl_gives_sasl_ssl(self):
        cfg = self._build("b:9092", "cid", True, "user", "pass")
        assert cfg["security.protocol"] == "SASL_SSL"

    def test_broker_whitespace_trimmed(self):
        cfg = self._build("b1:9092, b2:9092, b3:9092", "cid", False, None, None)
        assert cfg["bootstrap.servers"] == "b1:9092,b2:9092,b3:9092"

    def test_sasl_credentials_included_when_set(self):
        cfg = self._build("b:9092", "cid", False, "user", "pass")
        assert cfg["sasl.mechanism"] == "PLAIN"
        assert cfg["sasl.username"] == "user"
        assert cfg["sasl.password"] == "pass"

    def test_sasl_keys_absent_when_no_credentials(self):
        cfg = self._build("b:9092", "cid", False, None, None)
        assert "sasl.username" not in cfg
        assert "sasl.password" not in cfg

    def test_sasl_omitted_when_only_username_set(self):
        cfg = self._build("b:9092", "cid", False, "user", None)
        assert "sasl.username" not in cfg

    def test_client_id_set(self):
        cfg = self._build("b:9092", "my-service", False, None, None)
        assert cfg["client.id"] == "my-service"


class TestProducerConfigViaEnv:
    """Integration: verify env vars are mapped to Producer config correctly."""

    def test_default_client_id(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()
        mock_ck = _make_confluent_kafka_mock(mock_instance)

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        cfg = mock_ck.Producer.call_args[0][0]
        assert cfg["client.id"] == "fulcrum-plugin"

    def test_custom_client_id_from_env(self, monkeypatch):
        _set_kafka_env(monkeypatch, FULCRUM_KAFKA_CLIENT_ID="my-service")
        mock_instance = _make_mock_producer()
        mock_ck = _make_confluent_kafka_mock(mock_instance)

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        cfg = mock_ck.Producer.call_args[0][0]
        assert cfg["client.id"] == "my-service"

    def test_ssl_disabled_by_default(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer()
        mock_ck = _make_confluent_kafka_mock(mock_instance)

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        cfg = mock_ck.Producer.call_args[0][0]
        assert cfg["security.protocol"] == "PLAINTEXT"

    def test_ssl_enabled_via_env(self, monkeypatch):
        _set_kafka_env(monkeypatch, FULCRUM_KAFKA_SSL="true")
        mock_instance = _make_mock_producer()
        mock_ck = _make_confluent_kafka_mock(mock_instance)

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        cfg = mock_ck.Producer.call_args[0][0]
        assert cfg["security.protocol"] == "SSL"

    def test_sasl_config_when_both_credentials_set(self, monkeypatch):
        _set_kafka_env(
            monkeypatch,
            FULCRUM_KAFKA_SASL_USERNAME="user",
            FULCRUM_KAFKA_SASL_PASSWORD="pass",
        )
        mock_instance = _make_mock_producer()
        mock_ck = _make_confluent_kafka_mock(mock_instance)

        with patch.dict("sys.modules", {"confluent_kafka": mock_ck}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        cfg = mock_ck.Producer.call_args[0][0]
        assert cfg["sasl.mechanism"] == "PLAIN"
        assert cfg["sasl.username"] == "user"
        assert cfg["sasl.password"] == "pass"


# ---------------------------------------------------------------------------
# TestErrorHandling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_no_raise_when_produce_fails(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer(produce_error=RuntimeError("broker unavailable"))

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)  # must not raise

    def test_flush_called_even_when_produce_fails(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer(produce_error=RuntimeError("broker unavailable"))

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)

        mock_instance.flush.assert_called_once()

    def test_no_raise_when_confluent_kafka_not_installed(self, monkeypatch):
        _set_kafka_env(monkeypatch)

        with patch.dict("sys.modules", {"confluent_kafka": None}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)  # ImportError must be caught, not raised

    def test_no_raise_when_flush_fails(self, monkeypatch):
        _set_kafka_env(monkeypatch)
        mock_instance = _make_mock_producer(flush_error=RuntimeError("flush error"))

        with patch.dict("sys.modules", {"confluent_kafka": _make_confluent_kafka_mock(mock_instance)}):
            kp = _reload_kp()
            kp.send_event(**FIXED_FIELDS)  # must not raise
