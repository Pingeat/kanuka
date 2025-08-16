const { getLogger } = require('../utils/logger');
const logger = getLogger('whatsapp_service');

async function sendTextMessage(to, message) {
  logger.info(`Sending message to ${to}: ${message}`);
  // TODO: integrate with WhatsApp API
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
  sendPaymentLink
};
