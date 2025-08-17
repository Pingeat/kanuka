const test = require('node:test');
const assert = require('assert');
const crypto = require('crypto');

const { getBrandIdFromSignature } = require('../handlers/paymentWebhook');

test('getBrandIdFromSignature selects correct brand based on signature', () => {
  process.env.RAZORPAY_WEBHOOK_SECRET_KANUKA = 'secretkanuka';
  process.env.RAZORPAY_WEBHOOK_SECRET_ZUMI = 'secretzumi';
  const payload = JSON.stringify({ test: true });
  const sig = crypto
    .createHmac('sha256', 'secretzumi')
    .update(payload)
    .digest('hex');

  const brand = getBrandIdFromSignature(payload, sig);
  assert.strictEqual(brand, 'zumi');
});

test('getBrandIdFromSignature falls back to default secret', () => {
  delete process.env.RAZORPAY_WEBHOOK_SECRET_ZUMI;
  delete process.env.RAZORPAY_WEBHOOK_SECRET_KANUKA;
  const payload = JSON.stringify({ test: true });
  const sig = crypto
    .createHmac('sha256', 'kanuka')
    .update(payload)
    .digest('hex');

  const brand = getBrandIdFromSignature(payload, sig);
  assert.strictEqual(brand, 'kanuka');
});

test('getBrandIdFromSignature returns null for unknown signature', () => {
  process.env.RAZORPAY_WEBHOOK_SECRET_KANUKA = 'secretkanuka';
  process.env.RAZORPAY_WEBHOOK_SECRET_ZUMI = 'secretzumi';
  const payload = JSON.stringify({ test: true });
  const sig = crypto
    .createHmac('sha256', 'invalidsecret')
    .update(payload)
    .digest('hex');

  const brand = getBrandIdFromSignature(payload, sig);
  assert.strictEqual(brand, null);
});
