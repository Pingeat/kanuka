require('dotenv').config();
const { getLogger } = require('../utils/logger');
const { BRANCH_CONTACTS, OTHER_NUMBERS } = require('../config/settings');
const redisState = require('../stateHandlers/redisState');

const logger = getLogger('whatsapp_service');

// Construct the WhatsApp API URL from the phone number ID to avoid relying on
// string interpolation inside environment files which aren't parsed by
// `dotenv`.
const phoneNumberId = process.env.META_PHONE_NUMBER_ID;
if (!phoneNumberId) {
  logger.error('META_PHONE_NUMBER_ID is not defined');
}
const WHATSAPP_API_URL = `https://graph.facebook.com/v23.0/${phoneNumberId}/messages`;

async function sendTextMessage(to, message) {
  logger.info(`Sending message to ${to}`);
  const payload = {
    messaging_product: 'whatsapp',
    to,
    type: 'text',
    text: { preview_url: false, body: message }
  };

  try {
    const res = await fetch(WHATSAPP_API_URL, {
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
  const message =
    '🌟 *EXPLORE OUR PRODUCTS*\n\n' +
    'Browse our catalog and select items to add to your cart.\n\n' +
    'Tap the button below to view our catalog:';

  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to,
    type: 'interactive',
    interactive: {
      type: 'catalog_message',
      body: { text: message },
      action: {
        name: 'catalog_message',
        catalog_id: process.env.CATALOG_ID,
      },
    },
  };

  try {
    const res = await fetch(WHATSAPP_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.META_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    logger.info(`Catalog template sent. Status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Catalog error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send catalog: ${err.message}`);
    throw err;
  }
}

async function sendOrderConfirmation(to, orderId) {
  logger.info(`Sending order confirmation for ${orderId} to ${to}`);
  const order = await redisState.getOrder(orderId);
  if (!order) {
    await sendTextMessage(to, `Order #${orderId} not found.`);
    return;
  }

  let message =
    `✅ *ORDER CONFIRMED*\n\n` +
    `Order ID: #${order.order_id}\n` +
    `Branch: ${order.branch}\n` +
    `Payment Method: ${order.payment_method}\n\n` +
    'ORDER ITEMS:\n';

  for (const item of order.items) {
    const itemTotal = item.price * item.quantity;
    message += `• ${item.name} x${item.quantity} = ₹${itemTotal}\n`;
  }

  message += `\n*TOTAL*: ₹${Math.ceil(order.total)}\n\n`;
  message += 'Your order will be processed shortly. Thank you for shopping with Kanuka Organics!';

  await sendTextMessage(to, message);
}

async function sendMainMenu(to) {
  const message = 'Welcome to Kanuka Organics!';
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to,
    type: 'interactive',
    interactive: {
      type: 'button',
      body: { text: message },
      action: {
        buttons: [
          {
            type: 'reply',
            reply: { id: 'ORDER_NOW', title: '🛍️ Order Now' },
          },
        ],
      },
    },
  };

  try {
    const res = await fetch(WHATSAPP_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.META_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    logger.info(`Main menu sent. Status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Main menu error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send main menu: ${err.message}`);
    throw err;
  }
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
