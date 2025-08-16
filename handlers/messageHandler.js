const redisState = require('../stateHandlers/redisState');
const { sendTextMessage, sendCatalog, sendOrderConfirmation } = require('../services/whatsappService');
const { placeOrder, isWithinDeliveryRadius } = require('../services/orderService');
const { getLogger } = require('../utils/logger');
const logger = getLogger('message_handler');

async function handleIncomingMessage(data) {
  try {
    for (const entry of data.entry || []) {
      for (const change of entry.changes || []) {
        const value = change.value || {};
        const messages = value.messages || [];
        if (!messages.length) continue;
        const msg = messages[0];
        const sender = msg.from;
        const type = msg.type;
        if (type === 'text') {
          const text = msg.text.body.trim().toLowerCase();
          if (text === 'catalog') {
            await sendCatalog(sender);
          } else {
            await sendTextMessage(sender, 'Unsupported command');
          }
        } else if (type === 'location') {
          const { latitude, longitude } = msg.location;
          await redisState.setLocation(sender, latitude, longitude);
          const { within, branch } = isWithinDeliveryRadius(latitude, longitude);
          if (within) {
            await sendTextMessage(sender, `Nearest branch: ${branch}`);
          } else {
            await sendTextMessage(sender, 'Sorry, we do not deliver to your location');
          }
        } else if (type === 'order') {
          const orderRes = await placeOrder(sender, 'Delivery');
          if (orderRes.success) {
            await sendOrderConfirmation(sender, orderRes.order_id);
          }
        }
      }
    }
    return { status: 'ok' };
  } catch (err) {
    logger.error(`handleIncomingMessage error: ${err}`);
    return { status: 'error' };
  }
}

module.exports = { handleIncomingMessage };
