const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { sendEvent } = require('./kafka-producer');

// ---------------------------------------------------------------------------
// Helper: creates a controllable mock Kafka stack and records all calls.
// ---------------------------------------------------------------------------
function createMockKafkaFactory({ connectError, sendError, disconnectError } = {}) {
  const calls = {
    factoryConfigs: [],
    connect:        0,
    sends:          [],
    disconnect:     0,
  };

  const producer = {
    connect:    async () => { calls.connect++;    if (connectError)    throw connectError;    },
    send:       async (msg) => { calls.sends.push(msg); if (sendError)    throw sendError;       },
    disconnect: async () => { calls.disconnect++; if (disconnectError) throw disconnectError; },
  };

  const factory = (config) => {
    calls.factoryConfigs.push(config);
    return { producer: () => producer };
  };

  return { factory, calls };
}

// ---------------------------------------------------------------------------
// Env helpers
// ---------------------------------------------------------------------------
let savedEnv;
function saveEnv()    { savedEnv = { ...process.env }; }
function restoreEnv() { for (const k of Object.keys(process.env)) delete process.env[k]; Object.assign(process.env, savedEnv); }

function setKafkaEnv(overrides = {}) {
  process.env.FULCRUM_KAFKA_BROKERS = 'broker1:9092,broker2:9092';
  process.env.FULCRUM_KAFKA_TOPIC   = 'fulcrum-metrics';
  delete process.env.FULCRUM_KAFKA_CLIENT_ID;
  delete process.env.FULCRUM_KAFKA_SSL;
  delete process.env.FULCRUM_KAFKA_SASL_USERNAME;
  delete process.env.FULCRUM_KAFKA_SASL_PASSWORD;
  Object.assign(process.env, overrides);
}

// Fixed fields shared by most tests
const fixedFields = {
  eventType:     'workflow.session.started',
  sessionId:     'abc-123',
  project:       'checkout-service',
  pluginVersion: '1.2.0',
};

// ===========================================================================
// sendEvent — missing config
// ===========================================================================
describe('sendEvent — missing config', () => {
  beforeEach(saveEnv);
  afterEach(restoreEnv);

  it('skips when FULCRUM_KAFKA_BROKERS is not set', async () => {
    setKafkaEnv();
    delete process.env.FULCRUM_KAFKA_BROKERS;

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs.length, 0, 'factory must not be called');
  });

  it('skips when FULCRUM_KAFKA_TOPIC is not set', async () => {
    setKafkaEnv();
    delete process.env.FULCRUM_KAFKA_TOPIC;

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs.length, 0, 'factory must not be called');
  });

  it('skips when both required env vars are absent', async () => {
    delete process.env.FULCRUM_KAFKA_BROKERS;
    delete process.env.FULCRUM_KAFKA_TOPIC;

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs.length, 0, 'factory must not be called');
  });
});

// ===========================================================================
// sendEvent — happy path
// ===========================================================================
describe('sendEvent — happy path', () => {
  beforeEach(saveEnv);
  afterEach(restoreEnv);

  it('sends a message with all fixed fields in the payload', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, { outcome: 'in_progress' }, factory);

    assert.equal(calls.sends.length, 1);
    const msg   = calls.sends[0];
    const value = JSON.parse(msg.messages[0].value);

    assert.equal(value.event_type,     fixedFields.eventType);
    assert.equal(value.session_id,     fixedFields.sessionId);
    assert.equal(value.project,        fixedFields.project);
    assert.equal(value.plugin_version, fixedFields.pluginVersion);
    assert.ok(value.timestamp, 'timestamp must be present');
  });

  it('places event-specific data in the metadata field', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    const metadata = { outcome: 'branch_finished', commits_count: 3 };
    await sendEvent(fixedFields, metadata, factory);

    const value = JSON.parse(calls.sends[0].messages[0].value);
    assert.deepEqual(value.metadata, metadata);
  });

  it('uses session_id as the message key', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.sends[0].messages[0].key, fixedFields.sessionId);
  });

  it('sends to the topic from env', async () => {
    setKafkaEnv({ FULCRUM_KAFKA_TOPIC: 'my-custom-topic' });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.sends[0].topic, 'my-custom-topic');
  });

  it('calls connect then send then disconnect in order', async () => {
    setKafkaEnv();
    const order = [];

    const orderedFactory = () => ({
      producer: () => ({
        connect:    async () => order.push('connect'),
        send:       async () => order.push('send'),
        disconnect: async () => order.push('disconnect'),
      }),
    });

    await sendEvent(fixedFields, {}, orderedFactory);
    assert.deepEqual(order, ['connect', 'send', 'disconnect']);
  });
});

// ===========================================================================
// sendEvent — Kafka client config
// ===========================================================================
describe('sendEvent — Kafka client config', () => {
  beforeEach(saveEnv);
  afterEach(restoreEnv);

  it('parses comma-separated brokers into an array', async () => {
    setKafkaEnv({ FULCRUM_KAFKA_BROKERS: 'b1:9092, b2:9092, b3:9092' });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.deepEqual(calls.factoryConfigs[0].brokers, ['b1:9092', 'b2:9092', 'b3:9092']);
  });

  it('uses "fulcrum-plugin" as default client ID', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].clientId, 'fulcrum-plugin');
  });

  it('uses FULCRUM_KAFKA_CLIENT_ID when set', async () => {
    setKafkaEnv({ FULCRUM_KAFKA_CLIENT_ID: 'my-service' });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].clientId, 'my-service');
  });

  it('disables SSL by default', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].ssl, false);
  });

  it('enables SSL when FULCRUM_KAFKA_SSL=true', async () => {
    setKafkaEnv({ FULCRUM_KAFKA_SSL: 'true' });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].ssl, true);
  });

  it('includes SASL config when both credentials are set', async () => {
    setKafkaEnv({
      FULCRUM_KAFKA_SASL_USERNAME: 'user',
      FULCRUM_KAFKA_SASL_PASSWORD: 'pass',
    });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.deepEqual(calls.factoryConfigs[0].sasl, {
      mechanism: 'plain',
      username:  'user',
      password:  'pass',
    });
  });

  it('omits SASL config when credentials are absent', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].sasl, undefined);
  });

  it('omits SASL config when only username is set', async () => {
    setKafkaEnv({ FULCRUM_KAFKA_SASL_USERNAME: 'user' });

    const { factory, calls } = createMockKafkaFactory();
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.factoryConfigs[0].sasl, undefined);
  });
});

// ===========================================================================
// sendEvent — error handling
// ===========================================================================
describe('sendEvent — error handling', () => {
  beforeEach(saveEnv);
  afterEach(restoreEnv);

  it('does not throw when producer.connect() fails', async () => {
    setKafkaEnv();

    const { factory } = createMockKafkaFactory({ connectError: new Error('connection refused') });
    await assert.doesNotReject(() => sendEvent(fixedFields, {}, factory));
  });

  it('does not throw when producer.send() fails', async () => {
    setKafkaEnv();

    const { factory } = createMockKafkaFactory({ sendError: new Error('broker unavailable') });
    await assert.doesNotReject(() => sendEvent(fixedFields, {}, factory));
  });

  it('still calls disconnect when producer.send() fails', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory({ sendError: new Error('broker unavailable') });
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.disconnect, 1, 'disconnect must be called even after send error');
  });

  it('still calls disconnect when producer.connect() fails', async () => {
    setKafkaEnv();

    const { factory, calls } = createMockKafkaFactory({ connectError: new Error('timeout') });
    await sendEvent(fixedFields, {}, factory);

    assert.equal(calls.disconnect, 1, 'disconnect must be called even after connect error');
  });

  it('does not throw when producer.disconnect() itself fails', async () => {
    setKafkaEnv();

    const { factory } = createMockKafkaFactory({ disconnectError: new Error('disconnect error') });
    await assert.doesNotReject(() => sendEvent(fixedFields, {}, factory));
  });
});

