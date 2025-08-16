const redisState = require('../stateHandlers/redisState');
const { sendCartReminder } = require('../services/whatsappService');
const { getLogger } = require('../utils/logger');

const logger = getLogger('reminder_scheduler');

async function processReminderQueue() {
  const reminder = await redisState.popReminder();
  if (!reminder) return;
  const { userId, cart } = reminder;
  await sendCartReminder(userId, cart);
  logger.info(`Processed reminder for ${userId}`);
}

async function enqueueDailyReminders() {
  const users = await redisState.getUsersWithCarts();
  for (const userId of users) {
    const cart = await redisState.getCart(userId);
    if (cart.items && cart.items.length) {
      await redisState.pushReminder({ userId, cart });
    }
  }
  logger.info('Daily reminders queued');
}

function startReminderScheduler() {
  setInterval(processReminderQueue, 60 * 1000);
  setInterval(enqueueDailyReminders, 24 * 60 * 60 * 1000);
  logger.info('Reminder scheduler started');
}

module.exports = { startReminderScheduler };
