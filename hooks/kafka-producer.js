/**
 * Shared Kafka producer for Fulcrum metrics hooks.
 *
 * kafkajs is vendored in hooks/vendor/kafkajs — no install step required.
 *
 * Config is read from environment variables at call time:
 *
 *   FULCRUM_KAFKA_BROKERS        Comma-separated broker list (required)
 *   FULCRUM_KAFKA_TOPIC          Topic name for all events (required)
 *   FULCRUM_KAFKA_CLIENT_ID      Producer client ID (default: "fulcrum-plugin")
 *   FULCRUM_KAFKA_SSL            Enable TLS — "true" or "false" (default: "false")
 *   FULCRUM_KAFKA_SASL_USERNAME  SASL plain username (optional)
 *   FULCRUM_KAFKA_SASL_PASSWORD  SASL plain password (optional)
 */

const path = require('path');

function defaultKafkaFactory(config) {
  const { Kafka } = require(path.join(__dirname, 'vendor', 'kafkajs'));
  return new Kafka(config);
}

/**
 * Send a single event to the configured Kafka topic.
 *
 * Fixed fields (common to every event):
 * @param {string} eventType      e.g. "workflow.session.started"
 * @param {string} sessionId      UUID of the current session
 * @param {string} project        Project name derived from git remote
 * @param {string} pluginVersion  Version string from plugin.json
 *
 * @param {object} metadata       Event-specific payload (may be empty)
 *
 * @param {function} [kafkaFactory]  Injected in tests to avoid a real broker
 *
 * Skips silently when required env vars are not set.
 */
async function sendEvent(
  { eventType, sessionId, project, pluginVersion },
  metadata = {},
  kafkaFactory = defaultKafkaFactory
) {
  const brokers = process.env.FULCRUM_KAFKA_BROKERS;
  const topic   = process.env.FULCRUM_KAFKA_TOPIC;

  if (!brokers || !topic) {
    console.warn('[metrics] Kafka not configured — skipping event emission (set FULCRUM_KAFKA_BROKERS and FULCRUM_KAFKA_TOPIC)');
    return;
  }

  const clientId = process.env.FULCRUM_KAFKA_CLIENT_ID || 'fulcrum-plugin';
  const ssl      = process.env.FULCRUM_KAFKA_SSL === 'true';

  const saslUser = process.env.FULCRUM_KAFKA_SASL_USERNAME;
  const saslPass = process.env.FULCRUM_KAFKA_SASL_PASSWORD;
  const sasl     = saslUser && saslPass
    ? { mechanism: 'plain', username: saslUser, password: saslPass }
    : undefined;

  const kafkaConfig = {
    clientId,
    brokers: brokers.split(',').map((b) => b.trim()),
    ssl,
    sasl,
  };

  const kafka    = kafkaFactory(kafkaConfig);
  const producer = kafka.producer();

  const payload = {
    event_type:     eventType,
    timestamp:      new Date().toISOString(),
    session_id:     sessionId,
    project,
    plugin_version: pluginVersion,
    metadata,
  };

  try {
    await producer.connect();
    await producer.send({
      topic,
      messages: [{ key: sessionId, value: JSON.stringify(payload) }],
    });
  } catch (err) {
    console.error('[metrics] Kafka emission failed:', err.message);
  } finally {
    await producer.disconnect().catch(() => {});
  }
}

module.exports = { sendEvent };
