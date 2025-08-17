const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { confirmOrder } = require('../services/orderService');
const {
  sendTextMessage,
  setBrandContext
} = require('../services/whatsappService');
const { loadBrandConfig } = require('../services/brandService');
const { setBrandCatalog } = require('../config/settings');
const { getLogger } = require('../utils/logger');

const logger = getLogger('payment_webhook');

function verifySignature(rawBody, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');
  return expected === signature;
}

function getBrandIdFromSignature(rawBody, signature) {
  const brandsDir = path.join(__dirname, '..', 'config', 'brands');
  const files = fs.readdirSync(brandsDir);
  for (const file of files) {
    const brandId = path.basename(file, '.json');
    // Skip the default brand; it will be checked separately as a fallback
    if (brandId === 'kanuka') continue;
    const secret = process.env[`RAZORPAY_WEBHOOK_SECRET_${brandId.toUpperCase()}`];
    if (secret && verifySignature(rawBody, signature, secret)) {
      return brandId;
    }
  }

  const defaultSecret = process.env.RAZORPAY_WEBHOOK_SECRET_KANUKA;
  if (defaultSecret && verifySignature(rawBody, signature, defaultSecret)) {
    return 'kanuka';
  }

  return null;
}

async function handlePaymentWebhook(req, res) {
  const signature = req.get('X-Razorpay-Signature');
  const brandId = signature ? getBrandIdFromSignature(req.rawBody, signature) : null;
  if (!brandId) {
    logger.warn('Invalid Razorpay signature');
    res.send('Ignored');
    return;
  }

  const brandConfig = loadBrandConfig(brandId) || {};
  const upper = brandId.toUpperCase();
  const phoneId = process.env[`META_PHONE_NUMBER_ID_${upper}`];
  const catalogId = process.env[`CATALOG_ID_${upper}`];
  const accessToken = process.env[`META_ACCESS_TOKEN_${upper}`];
  setBrandContext(brandConfig, phoneId, catalogId, accessToken);
  setBrandCatalog(brandConfig);

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

module.exports = { handlePaymentWebhook, getBrandIdFromSignature };
