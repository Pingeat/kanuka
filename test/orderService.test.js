const test = require('node:test');
const assert = require('node:assert');
const { generateOrderId } = require('../services/orderService');
const redisState = require('../stateHandlers/redisState');

test('generateOrderId returns value with ORD prefix', () => {
  const id = generateOrderId();
  assert.ok(id.startsWith('ORD'));
});

test.after(() => {
  redisState.redis.disconnect();
});
