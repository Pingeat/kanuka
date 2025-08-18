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
  if (!secret || !rawBody || !signature) {
    return false;
  }

  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  const expectedBuf = Buffer.from(expected, 'utf8');
  const signatureBuf = Buffer.from(signature, 'utf8');
  if (expectedBuf.length !== signatureBuf.length) {
    return false;
  }
  return crypto.timingSafeEqual(expectedBuf, signatureBuf);
}

async function handlePaymentWebhook(req, res) {
  const { confirmOrder } = require('../services/orderService');
  const { sendTextMessage, setBrandContext } = require('../services/whatsappService');
  const { loadBrandConfig } = require('../services/brandService');
  const { setBrandCatalog } = require('../config/settings');
  const signature = req.get('X-Razorpay-Signature');
  const data = req.body || {};
  const payment = data.payload?.payment_link?.entity || {};
  const orderId = payment.reference_id;

  let order = null;
  let brandId = null;
  let secret = process.env.RAZORPAY_WEBHOOK_SECRET;

  if (orderId) {
    order = await getRedis().getOrder(orderId);
    brandId = order?.brand_id;
    if (brandId) {
      const brandSecret =
        process.env[`RAZORPAY_WEBHOOK_SECRET_${brandId.toUpperCase()}`];
      if (brandSecret) {
        secret = brandSecret;
      }
    }
  }

  if (!secret) {
    logger.error('Razorpay webhook secret is not configured');
    res.status(500).send('Server misconfigured');
    return;
  }

  if (!signature || !verifySignature(req.rawBody, signature, secret)) {
    logger.warn('Invalid Razorpay signature, ignoring payment');
    res.status(200).send('Ignored');
    return;
  }

  if (data.event === 'payment_link.paid') {
    const whatsapp = payment.customer?.contact;

    if (whatsapp && orderId) {
      if (!brandId) {
        logger.warn(
          `Skipping notification: brand not found for order ${orderId}`
        );
        return res.send('OK');
      }

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
