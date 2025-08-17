const redisState = require('../stateHandlers/redisState');
const { sendCartReminder, setBrandContext } = require('../services/whatsappService');
const { setBrandCatalog } = require('../config/settings');
const { getBrandInfoByPhoneId } = require('../config/brandConfig');
const { getLogger } = require('../utils/logger');

const logger = getLogger('cart_reminder');

async function checkCartReminders() {
  const {
    brandConfig,
    brandId,
    phoneNumberId,
    catalogId,
    accessToken,
  } = getBrandInfoByPhoneId(process.env.META_PHONE_NUMBER_ID);
  setBrandContext(brandConfig, phoneNumberId, catalogId, accessToken);
  setBrandCatalog(brandConfig);

  const users = await redisState.getUsersWithCarts(brandId);
  const now = new Date();
  const today = now.toISOString().slice(0, 10);

  for (const userId of users) {
    const cart = await redisState.getCart(userId, brandId);
    if (!cart.items || cart.items.length === 0) {
      await redisState.clearCart(userId, brandId);
      continue;
    }
    if (!cart.lastAdded) continue;
    const lastAdded = new Date(cart.lastAdded);
    const diffMs = now - lastAdded;
    if (diffMs >= 60 * 60 * 1000 && cart.lastReminderDate !== today) {
      await sendCartReminder(userId, cart);
      await redisState.markCartReminderSent(userId, today, brandId);
      logger.info(`Sent cart reminder to ${userId}`);
    }
  }
}

function startCartReminderScheduler() {
  setInterval(checkCartReminders, 60 * 1000);
  logger.info('Cart reminder scheduler started');
}

module.exports = { startCartReminderScheduler };
