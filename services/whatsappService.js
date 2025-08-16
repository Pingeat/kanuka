require('dotenv').config();
const { getLogger } = require('../utils/logger');
const { BRANCH_CONTACTS, OTHER_NUMBERS, ORDER_STATUS } = require('../config/settings');
const redisState = require('../stateHandlers/redisState');

const logger = getLogger('whatsapp_service');

let brandConfig = { name: 'Kanuka Organics', catalog: [] };
let phoneNumberId = process.env.META_PHONE_NUMBER_ID;
let catalogId = process.env.CATALOG_ID;
let WHATSAPP_API_URL = phoneNumberId
  ? `https://graph.facebook.com/v23.0/${phoneNumberId}/messages`
  : null;

function setBrandContext(config, phoneId, catId) {
  brandConfig = config || brandConfig;
  phoneNumberId = phoneId || phoneNumberId;
  catalogId = catId || catalogId;
  WHATSAPP_API_URL = `https://graph.facebook.com/v23.0/${phoneNumberId}/messages`;
}

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
    '🌟 *Explore Our Organic Products* 🌿\n\n' +
    'Browse our catalog and add your favourites to the cart.\n\n' +
    '👇 Tap below to get started!';

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
        catalog_id: catalogId,
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
    `✅ *ORDER CONFIRMED* 🎉\n\n` +
    `📦 Order ID: #${order.order_id}\n` +
    `🏪 Branch: ${order.branch}\n` +
    `💳 Payment Method: ${order.payment_method}\n\n` +
    '🛍️ *ORDER ITEMS*:\n';

  for (const item of order.items) {
    const itemTotal = item.price * item.quantity;
    message += `• ${item.name} x${item.quantity} = ₹${itemTotal}\n`;
  }

  if (order.discount_percentage && order.discount_percentage > 0) {
    message +=
      `\nSubtotal: ₹${Math.ceil(order.actual_total)}\n` +
      `Discount (${Math.ceil(order.discount_percentage)}%): -₹${Math.ceil(
        order.discount_amount
      )}\n`;
  }
  message += `\n*TOTAL PAYABLE*: ₹${Math.ceil(order.total)}\n\n`;
  message += `🙏 Thanks for shopping with ${brandConfig.name}!`;

  await sendTextMessage(to, message);
}

async function sendMainMenu(to) {
  const message = `🌿 Welcome to *${brandConfig.name}*! 🌿\nHow can we assist you today?`;
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
            reply: { id: 'ORDER_NOW', title: '🛍️ Shop Now' },
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

  const lines = cart.items.map(
    (i) => `• ${i.quantity} × ${i.name} = ₹${i.price * i.quantity}`
  );
  const message =
    `🛒 *Cart Summary*\n${lines.join('\n')}\n*Total*: ₹${cart.total}\n\nSelect an option below:`;

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
            reply: { id: 'CONTINUE_SHOPPING', title: '🛍️ Continue' }
          },
          {
            type: 'reply',
            reply: { id: 'PROCEED_TO_CHECKOUT', title: '✅ Checkout' }
          },
          {
            type: 'reply',
            reply: { id: 'CLEAR_CART', title: '🗑️ Clear Cart' }
          }
        ]
      }
    }
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
    logger.info(`Cart summary template sent. Status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Cart summary error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send cart summary: ${err.message}`);
    throw err;
  }
}

async function sendPaymentOptions(to) {
  const message =
    '💳 *Payment Options*\n\nPlease choose your preferred payment method:';

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
            reply: { id: 'PAY_ONLINE', title: '💳 Pay Online' }
          },
          {
            type: 'reply',
            reply: { id: 'PAY_CASH', title: '💵 Cash on Delivery' }
          }
        ]
      }
    }
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
    logger.info(`Payment options sent. Status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Payment options error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send payment options: ${err.message}`);
    throw err;
  }
}

async function sendLocationRequest(to) {
  await sendTextMessage(to, '📍 Please share your location to proceed.');
}

async function sendBranchSelection(to, branches) {
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to,
    type: 'interactive',
    interactive: {
      type: 'list',
      header: { type: 'text', text: 'Select Branch' },
      body: {
        text: 'Choose your preferred store branch:'
      },
      action: {
        button: 'Branches',
        sections: [
          {
            title: 'Available Branches',
            rows: branches.map((b) => ({ id: b, title: b }))
          }
        ]
      }
    }
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
    logger.info(`Branch selection sent. Status: ${res.status}`);
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Branch selection error: ${errText}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send branch selection: ${err.message}`);
    throw err;
  }
}

async function sendPaymentLink(to, link) {
  const token = link.split('/').pop();
  const payload = {
    messaging_product: 'whatsapp',
    to,
    type: 'template',
    template: {
      name: 'pays_online',
      language: { code: 'en_US' },
      components: [
        {
          type: 'button',
          sub_type: 'url',
          index: 0,
          parameters: [{ type: 'text', text: token }]
        }
      ]
    }
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
    if (!res.ok) {
      const errText = await res.text();
      logger.error(`Payment link template error: ${errText}`);
      await sendTextMessage(to, `Complete payment using this link: ${link}`);
    }
    return res;
  } catch (err) {
    logger.error(`Failed to send payment link template: ${err.message}`);
    await sendTextMessage(to, `Complete payment using this link: ${link}`);
  }
}

async function sendCartReminder(to, cart) {
  const items = cart.items.map(i => `${i.quantity} x ${i.name}`).join(', ');
  const message = `🛍️ You have items waiting in your cart: ${items}. ⚡ Complete your order!`;
  await sendTextMessage(to, message);
}

async function sendOrderAlert(
  branch,
  orderId,
  items,
  total,
  sender,
  deliveryAddress,
  deliveryType,
  paymentMethod,
  discountPercentage,
  discountAmount
) {
  logger.info(`Sending order alert to ${branch} for order ${orderId}`);
  const recipients = [
    ...(BRANCH_CONTACTS[branch] || []),
    ...OTHER_NUMBERS
  ];

  const lines = items
    .map((i) => `• ${i.quantity} x ${i.name} = ₹${i.price * i.quantity}`)
    .join('\n');
  let message =
    `🔔 *NEW ORDER ALERT*\n\n` +
    `Order ID: #${orderId}\n` +
    `Customer: ${sender}\n` +
    `Delivery Type: ${deliveryType}\n` +
    `Payment Method: ${paymentMethod}\n` +
    `Branch: ${branch}\n`;

  if (deliveryType === 'Delivery' && deliveryAddress) {
    message += `\nDELIVERY ADDRESS:\n${deliveryAddress}\n`;
  }

  message += `\nORDER ITEMS:\n${lines}\n\n`;
  if (discountPercentage && discountPercentage > 0) {
    message +=
      `Subtotal: ₹${Math.ceil(total + discountAmount)}\n` +
      `Discount (${Math.ceil(discountPercentage)}%): -₹${Math.ceil(
        discountAmount
      )}\n`;
  }
  message += `*TOTAL PAYABLE*: ₹${Math.ceil(total)}\n\nPlease prepare this order as soon as possible.`;

  for (const to of recipients) {
    await sendTextMessage(to, message);
  }
}

async function sendOrderStatusUpdate(to, orderId, status) {
  let message;
  switch (status) {
    case ORDER_STATUS.READY:
      message = `✅ Your order #${orderId} is ready for pickup.`;
      break;
    case ORDER_STATUS.ON_THE_WAY:
      message = `🚚 Your order #${orderId} is on the way.`;
      break;
    case ORDER_STATUS.DELIVERED:
      message = `📦 Your order #${orderId} has been delivered.`;
      break;
    default:
      message = `ℹ️ Order #${orderId} status: ${status}`;
  }
  await sendTextMessage(to, message);
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
  sendOrderAlert,
  sendOrderStatusUpdate,
  setBrandContext
};
