require('dotenv').config();
const { getLogger } = require('../utils/logger');
const { BRANCH_CONTACTS, OTHER_NUMBERS } = require('../config/settings');
const logger = getLogger('whatsapp_service');

async function sendTextMessage(to, message) {
  logger.info(`Sending message to ${to}`);
  const payload = {
    messaging_product: 'whatsapp',
    to,
    type: 'text',
    text: { preview_url: false, body: message }
  };

  try {
    const res = await fetch(process.env.WHATSAPP_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.META_ACCESS_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    logger.info(`WhatsApp API response status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`WhatsApp API error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send WhatsApp message: ${err.message}`);
    throw err;
  }
}

async function sendCatalog(to) {
  logger.info(`Sending catalog to ${to}`);
}

async function sendOrderConfirmation(to, orderId) {
  logger.info(`Sending order confirmation for ${orderId} to ${to}`);
}

async function sendMainMenu(to) {
  await sendTextMessage(to, 'Welcome to Kanuka! Reply with "catalog" to browse.');
}

async function sendCartSummary(to, cart) {
  if (!cart || !cart.items || cart.items.length === 0) {
    await sendTextMessage(to, 'Your cart is empty.');
    return;
  }
  const lines = cart.items.map(i => `${i.quantity} x ${i.name} = ${i.price * i.quantity}`);
  const message = `🛒 *Cart Summary*\n${lines.join('\n')}\nTotal: ${cart.total}`;
  await sendTextMessage(to, message);
}

async function sendPaymentOptions(to) {
  await sendTextMessage(to, 'Choose payment method: cash or online');
}

async function sendLocationRequest(to) {
  await sendTextMessage(to, 'Please share your location to proceed');
}

async function sendBranchSelection(to, branches) {
  await sendTextMessage(to, `Select branch: ${branches.join(', ')}`);
}

async function sendPaymentLink(to, link) {
  await sendTextMessage(to, `Complete payment using this link: ${link}`);
}

async function sendCartReminder(to, cart) {
  const items = cart.items.map(i => `${i.quantity} x ${i.name}`).join(', ');
  const message = `You have items waiting in your cart: ${items}. Complete your order!`;
  await sendTextMessage(to, message);
}

async function sendOrderAlert(branch, orderId, items, total, sender, deliveryAddress, deliveryType) {
  logger.info(`Sending order alert to ${branch} for order ${orderId}`);
  const recipients = [
    ...(BRANCH_CONTACTS[branch] || []),
    ...OTHER_NUMBERS
  ];

  const lines = items.map(i => `• ${i.quantity} x ${i.name} = ₹${i.price * i.quantity}`).join('\n');
  let message = `🔔 *NEW ORDER ALERT*\n\n` +
    `Order ID: #${orderId}\n` +
    `Customer: ${sender}\n` +
    `Delivery Type: ${deliveryType}\n` +
    `Branch: ${branch}\n`;

  if (deliveryType === 'Delivery' && deliveryAddress) {
    message += `\nDELIVERY ADDRESS:\n${deliveryAddress}\n`;
  }

  message += `\nORDER ITEMS:\n${lines}\n\n*TOTAL PAYABLE*: ₹${Math.ceil(total)}\n\nPlease prepare this order as soon as possible.`;

  for (const to of recipients) {
    await sendTextMessage(to, message);
  }
}

module.exports = {
  sendTextMessage,
  sendCatalog,
  sendOrderConfirmation,
  sendCartReminder,
  sendMainMenu,
  sendCartSummary,
  sendPaymentOptions,
  sendLocationRequest,
  sendBranchSelection,
  sendPaymentLink,
  sendOrderAlert
};
