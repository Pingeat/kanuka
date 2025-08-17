const test = require('node:test');
const assert = require('node:assert');
const { generateOrderId } = require('../services/orderService');

test('generateOrderId returns value with ORD prefix', () => {
const id = generateOrderId();
  assert.ok(id.startsWith('ORD'));
});


