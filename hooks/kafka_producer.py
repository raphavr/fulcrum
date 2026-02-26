"""
Shared Kafka producer for Fulcrum metrics hooks.

confluent-kafka is installed via hooks/requirements.txt — no vendoring required.

Config is read from environment variables at call time:

  FULCRUM_KAFKA_BROKERS        Comma-separated broker list (required)
  FULCRUM_KAFKA_TOPIC          Topic name for all events (required)
  FULCRUM_KAFKA_CLIENT_ID      Producer client ID (default: "fulcrum-plugin")
  FULCRUM_KAFKA_SSL            Enable TLS — "true" or "false" (default: "false")
  FULCRUM_KAFKA_SASL_USERNAME  SASL plain username (optional)
  FULCRUM_KAFKA_SASL_PASSWORD  SASL plain password (optional)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def _build_producer_config(
    brokers: str,
    client_id: str,
    ssl: bool,
    sasl_username: str | None,
    sasl_password: str | None,
) -> dict:
    """Pure function: maps env-var fields to a confluent-kafka Producer config dict."""
    has_sasl = bool(sasl_username and sasl_password)

    if ssl and has_sasl:
        security_protocol = "SASL_SSL"
    elif ssl:
        security_protocol = "SSL"
    elif has_sasl:
        security_protocol = "SASL_PLAINTEXT"
    else:
        security_protocol = "PLAINTEXT"

    # Normalize broker list (trim whitespace around each entry)
    bootstrap_servers = ",".join(b.strip() for b in brokers.split(","))

    config: dict = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": client_id,
        "security.protocol": security_protocol,
    }

    if has_sasl:
        config["sasl.mechanism"] = "PLAIN"
        config["sasl.username"] = sasl_username
        config["sasl.password"] = sasl_password

    return config


def send_event(
    event_type: str,
    session_id: str,
    project: str,
    plugin_version: str,
    metadata: dict | None = None,
) -> None:
    """
    Send a single event to the configured Kafka topic.

    Fixed fields (common to every event):
      event_type      e.g. "workflow.session.started"
      session_id      UUID of the current session
      project         Project name derived from git remote
      plugin_version  Version string from plugin.json

    metadata: event-specific payload (may be empty or None).

    Skips silently when required env vars are not set.
    """
    if metadata is None:
        metadata = {}

    brokers = os.environ.get("FULCRUM_KAFKA_BROKERS")
    topic = os.environ.get("FULCRUM_KAFKA_TOPIC")

    if not brokers or not topic:
        print(
            "[metrics] Kafka not configured — skipping event emission "
            "(set FULCRUM_KAFKA_BROKERS and FULCRUM_KAFKA_TOPIC)",
            file=sys.stderr,
        )
        return

    client_id = os.environ.get("FULCRUM_KAFKA_CLIENT_ID", "fulcrum-plugin")
    ssl = os.environ.get("FULCRUM_KAFKA_SSL", "false").lower() == "true"
    sasl_username = os.environ.get("FULCRUM_KAFKA_SASL_USERNAME") or None
    sasl_password = os.environ.get("FULCRUM_KAFKA_SASL_PASSWORD") or None

    config = _build_producer_config(brokers, client_id, ssl, sasl_username, sasl_password)

    payload = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "project": project,
        "plugin_version": plugin_version,
        "metadata": metadata,
    }

    key = session_id.encode()
    value = json.dumps(payload).encode()

    producer = None
    try:
        from confluent_kafka import Producer  # deferred: degrades gracefully if missing

        producer = Producer(config)
        producer.produce(topic=topic, key=key, value=value)
    except Exception as exc:
        print(f"[metrics] Kafka emission failed: {exc}", file=sys.stderr)
    finally:
        if producer is not None:
            try:
                undelivered = producer.flush(timeout=-1)
                if undelivered > 0:
                    print(
                        f"[metrics] flush: {undelivered} message(s) not delivered",
                        file=sys.stderr,
                    )
            except Exception:
                pass  # mirrors .catch(() => {}) on disconnect
