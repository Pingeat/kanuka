const redisState = require('../stateHandlers/redisState');
const { sendCartReminder } = require('../services/whatsappService');
const { getLogger } = require('../utils/logger');

const logger = getLogger('cart_reminder');

async function checkCartReminders() {
  const users = await redisState.getUsersWithCarts();
  const now = new Date();
  const today = now.toISOString().slice(0, 10);

  for (const userId of users) {
    const cart = await redisState.getCart(userId);
    if (!cart.items || cart.items.length === 0) {
      await redisState.clearCart(userId);
      continue;
    }
    if (!cart.lastAdded) continue;
    const lastAdded = new Date(cart.lastAdded);
    const diffMs = now - lastAdded;
    if (diffMs >= 60 * 60 * 1000 && cart.lastReminderDate !== today) {
      await sendCartReminder(userId, cart);
      await redisState.markCartReminderSent(userId, today);
      logger.info(`Sent cart reminder to ${userId}`);
    }
  }
}

function startCartReminderScheduler() {
  setInterval(checkCartReminders, 60 * 1000);
  logger.info('Cart reminder scheduler started');
}

module.exports = { startCartReminderScheduler };
