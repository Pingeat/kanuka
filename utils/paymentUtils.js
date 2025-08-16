const { getLogger } = require('./logger');
const logger = getLogger('payment_utils');

function generateRazorpayLink(amount, orderId) {
  // Placeholder for Razorpay payment link generation
  const paise = Math.round(amount * 100);
  const link = `https://razorpay.com/pay?order_id=${orderId}&amount=${paise}`;
  logger.info(`Generated payment link for ${orderId}`);
  return link;
}

module.exports = { generateRazorpayLink };
