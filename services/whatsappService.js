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

module.exports = {
  sendTextMessage,
  sendCatalog,
  sendOrderConfirmation
};
