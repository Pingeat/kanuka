const test = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');
const { verifySignature } = require('../handlers/paymentWebhook');

test('verifySignature validates correct signature', () => {
  const payload = JSON.stringify({ ok: true });
  const secret = 'secret';
  const sig = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  assert.ok(verifySignature(payload, sig, secret));
});

test('verifySignature rejects incorrect signature', () => {
  const payload = JSON.stringify({ ok: true });
  const secret = 'secret';
  const sig = crypto.createHmac('sha256', 'wrong').update(payload).digest('hex');
  assert.ok(!verifySignature(payload, sig, secret));
});
