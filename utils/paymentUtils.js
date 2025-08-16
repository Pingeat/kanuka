require('dotenv').config();
const { getLogger } = require('./logger');
const logger = getLogger('payment_utils');

async function generateRazorpayLink(amount, orderId, whatsapp) {
  const paise = Math.round(amount * 100);
  const auth = Buffer.from(
    `${process.env.RAZORPAY_KEY}:${process.env.RAZORPAY_SECRET}`
  ).toString('base64');

  // Format the contact number as per Razorpay requirements
  const contact = `+91${whatsapp.slice(-10)}`;

  try {
    const res = await fetch('https://api.razorpay.com/v1/payment_links', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Basic ${auth}`
      },
      body: JSON.stringify({
        amount: paise,
        currency: 'INR',
        accept_partial: false,
        reference_id: orderId,
        description: `Payment for order ${orderId}`,
        customer: {
          name: 'Customer',
          contact
        },
        notify: {
          sms: true,
          email: false
        },
        reminder_enable: true,
        callback_url:
          process.env.PAYMENT_SUCCESS_URL ||
          'https://example.com/payment-success',
        callback_method: 'get'
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error ? data.error.description : 'Failed to create payment link');
    }
    logger.info(`Generated payment link for ${orderId}`);
    return data.short_url;
  } catch (err) {
    logger.error(`Razorpay link generation failed: ${err.message}`);
    throw err;
  }
}

module.exports = { generateRazorpayLink };
