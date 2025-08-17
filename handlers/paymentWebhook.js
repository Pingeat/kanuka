const crypto = require('crypto');
const { getLogger } = require('../utils/logger');
let redisState = null;
function getRedis() {
  if (!redisState) {
    redisState = require('../stateHandlers/redisState');
  }
  return redisState;
}

const logger = getLogger('payment_webhook');

function verifySignature(rawBody, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');
  return expected === signature;
}

async function handlePaymentWebhook(req, res) {
  const { confirmOrder } = require('../services/orderService');
  const { sendTextMessage, setBrandContext } = require('../services/whatsappService');
  const { loadBrandConfig } = require('../services/brandService');
  const { setBrandCatalog } = require('../config/settings');
  const signature = req.get('X-Razorpay-Signature');
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
  if (!signature || !verifySignature(req.rawBody, signature, secret)) {
    logger.warn('Invalid Razorpay signature, ignoring payment');
    res.status(200).send('Ignored');
    return;
  }

  const data = req.body || {};
  if (data.event === 'payment_link.paid') {
    const payment = data.payload?.payment_link?.entity || {};
    const whatsapp = payment.customer?.contact;
    const orderId = payment.reference_id;

    if (whatsapp && orderId) {
      const order = await getRedis().getOrder(orderId);
      const brandId = order?.brand_id || 'kanuka';
      const brandConfig = loadBrandConfig(brandId) || {};
      const upper = brandId.toUpperCase();
      const phoneId = process.env[`META_PHONE_NUMBER_ID_${upper}`];
      const catalogId = process.env[`CATALOG_ID_${upper}`];
      const accessToken = process.env[`META_ACCESS_TOKEN_${upper}`];
      setBrandContext(brandConfig, phoneId, catalogId, accessToken);
      setBrandCatalog(brandConfig);

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

module.exports = { handlePaymentWebhook, verifySignature };
