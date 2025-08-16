const test = require('node:test');
const assert = require('assert');
const crypto = require('crypto');

process.env.RAZORPAY_WEBHOOK_SECRET_KANUKA = 'secretkanuka';
process.env.RAZORPAY_WEBHOOK_SECRET_ZUMI = 'secretzumi';

const { getBrandIdFromSignature } = require('../handlers/paymentWebhook');

test('getBrandIdFromSignature selects correct brand based on signature', () => {
  const payload = JSON.stringify({ test: true });
  const sig = crypto
    .createHmac('sha256', 'secretzumi')
    .update(payload)
    .digest('hex');

  const brand = getBrandIdFromSignature(payload, sig);
  assert.strictEqual(brand, 'zumi');
});

test('getBrandIdFromSignature returns null for unknown signature', () => {
  const payload = JSON.stringify({ test: true });
  const sig = crypto
    .createHmac('sha256', 'invalidsecret')
    .update(payload)
    .digest('hex');

  const brand = getBrandIdFromSignature(payload, sig);
  assert.strictEqual(brand, null);
});

