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

async function sendCartReminder(to, cart) {
  const items = cart.items.map(i => `${i.quantity} x ${i.name}`).join(', ');
  const message = `You have items waiting in your cart: ${items}. Complete your order!`;
  await sendTextMessage(to, message);
}

module.exports = {
  sendTextMessage,
  sendCatalog,
  sendOrderConfirmation,
  sendCartReminder
};
