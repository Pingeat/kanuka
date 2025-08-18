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

test('verifySignature returns false when secret is missing', () => {
  const payload = JSON.stringify({ ok: true });
  const secret = undefined;
  const sig = crypto.createHmac('sha256', 'secret').update(payload).digest('hex');
  assert.strictEqual(verifySignature(payload, sig, secret), false);
});

test('verifySignature returns false for mismatched length', () => {
  const payload = JSON.stringify({ ok: true });
  const secret = 'secret';
  const sig = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  // remove last character to create length mismatch
  assert.strictEqual(
    verifySignature(payload, sig.slice(0, -1), secret),
    false
  );
});
