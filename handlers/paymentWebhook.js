const crypto = require('crypto');
const { confirmOrder } = require('../services/orderService');
const { sendTextMessage } = require('../services/whatsappService');
const { getLogger } = require('../utils/logger');

const logger = getLogger('payment_webhook');

function verifySignature(rawBody, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');
  return expected === signature;
}

async function handlePaymentWebhook(req, res) {
  const signature = req.get('X-Razorpay-Signature');
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
  if (!signature || !secret || !verifySignature(req.rawBody, signature, secret)) {
    logger.warn('Invalid Razorpay signature');
    res.status(400).send('Invalid signature');
    return;
  }

  const data = req.body || {};
  if (data.event === 'payment_link.paid') {
    const payment = data.payload?.payment_link?.entity || {};
    const whatsapp = payment.customer?.contact;
    const orderId = payment.reference_id;

    if (whatsapp && orderId) {
      try {
        await sendTextMessage(
          whatsapp,
          '✅ Your payment is confirmed! Your order is being processed.'
        );
        await confirmOrder(whatsapp, orderId, 'Online');
      } catch (err) {
        logger.error(`Payment webhook processing failed: ${err.message}`);
      }
    }
  }

  res.send('OK');
}

module.exports = { handlePaymentWebhook };
