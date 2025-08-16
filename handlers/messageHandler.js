const redisState = require('../stateHandlers/redisState');
const {
  sendTextMessage,
  sendCatalog,
  sendOrderConfirmation,
  sendMainMenu,
  sendCartSummary,
  sendPaymentOptions,
  sendLocationRequest,
  sendBranchSelection,
  sendPaymentLink,
  setBrandContext
} = require('../services/whatsappService');
const { placeOrder, isWithinDeliveryRadius, updateOrderStatusFromCommand } = require('../services/orderService');
const { geocodeAddress } = require('../utils/geocode');
const { logUserActivity } = require('../utils/csvLogger');
const { PRODUCT_CATALOG, BRANCH_COORDINATES, setBrandCatalog } = require('../config/settings');
const { getBrandInfoByPhoneId } = require('../config/brandConfig');
const { getLogger } = require('../utils/logger');
const logger = getLogger('message_handler');

const STATES = {
  MAIN_MENU: 'MAIN_MENU',
  VIEWING_CATALOG: 'VIEWING_CATALOG',
  VIEWING_CART: 'VIEWING_CART',
  SELECTING_DELIVERY: 'SELECTING_DELIVERY',
  ENTERING_ADDRESS: 'ENTERING_ADDRESS',
  CHOOSING_PAYMENT: 'CHOOSING_PAYMENT'
};

async function handleText(sender, text, state) {
  logUserActivity(sender, 'message_received', text);

  if (state && state.step === STATES.ENTERING_ADDRESS) {
    await redisState.setAddress(sender, text);
    await sendPaymentOptions(sender);
    await redisState.setUserState(sender, { step: STATES.CHOOSING_PAYMENT });
    return;
  }

  if (state && state.step === STATES.SELECTING_DELIVERY) {
    const geo = await geocodeAddress(text);
    if (geo) {
      await redisState.setLocation(sender, geo.latitude, geo.longitude);
      const { within, branch } = isWithinDeliveryRadius(
        geo.latitude,
        geo.longitude
      );
      if (within) {
        await redisState.setBranch(sender, branch);
        await sendTextMessage(
          sender,
          `🎉 Great news! You're near our ${branch} branch. Please send your address.`
        );
        await redisState.setUserState(sender, {
          step: STATES.ENTERING_ADDRESS,
          address: ''
        });
      } else {
        await sendTextMessage(
          sender,
          '❌ Sorry, we do not deliver to that location.'
        );
      }
    } else {
      await sendTextMessage(sender, '❌ Sorry, we could not find that location.');
    }
    return;
  }

  const greetings = ['hi', 'hello', 'hey', 'hii', 'namaste'];
  if (greetings.some((g) => text.includes(g))) {
    await redisState.clearUserState(sender);
    await sendMainMenu(sender);
    await redisState.setUserState(sender, { step: STATES.MAIN_MENU });
    return;
  }

  if (text === 'menu') {
    await sendMainMenu(sender);
    await redisState.setUserState(sender, { step: STATES.MAIN_MENU });
  } else if (text === 'catalog') {
    await sendCatalog(sender);
    await redisState.setUserState(sender, { step: STATES.VIEWING_CATALOG });
  } else if (text === 'cart') {
    const cart = await redisState.getCart(sender);
    await sendCartSummary(sender, cart);
    await redisState.setUserState(sender, { step: STATES.VIEWING_CART });
  } else if (/^set discount \d+/.test(text)) {
    const value = parseInt(text.split(' ')[2]);
    await redisState.setGlobalDiscount(value);
    await sendTextMessage(sender, `🎯 Discount set to ${value}%!`);
  } else if (text === 'clear discount') {
    await redisState.clearGlobalDiscount();
    await sendTextMessage(sender, '✅ Discount cleared');
  } else {
    const res = await updateOrderStatusFromCommand(text);
    if (res.success) {
      await sendTextMessage(sender, res.message || '📦 Order status updated');
    } else if (res.message) {
      await sendTextMessage(sender, res.message);
    } else {
      await sendTextMessage(sender, '⚠️ Unsupported command');
    }
  }
}

async function handleListReply(sender, id) {
  await redisState.setBranch(sender, id);
  await sendTextMessage(sender, `📍 Branch selected: ${id}`);
  await sendCatalog(sender);
  await redisState.setUserState(sender, { step: STATES.VIEWING_CATALOG });
}

async function handleButtonReply(sender, id, state) {
  switch (id) {
    case 'ORDER_NOW': {
      await sendCatalog(sender);
      await redisState.setUserState(sender, { step: STATES.VIEWING_CATALOG });
      break;
    }
    case 'CONTINUE_SHOPPING': {
      await sendCatalog(sender);
      await redisState.setUserState(sender, { step: STATES.VIEWING_CATALOG });
      break;
    }
    case 'PROCEED_TO_CHECKOUT': {
      const discount = await redisState.getGlobalDiscount();
      if (discount) {
        await sendTextMessage(
          sender,
          `🎉 Congratulations! You've unlocked a ${discount}% discount.`
        );
      }
      await sendLocationRequest(sender);
      await redisState.setUserState(sender, { step: STATES.SELECTING_DELIVERY });
      break;
    }
    case 'CLEAR_CART': {
      await redisState.clearCart(sender);
      await sendTextMessage(sender, '🗑️ Your cart has been cleared.');
      await sendCatalog(sender);
      await redisState.setUserState(sender, { step: STATES.VIEWING_CATALOG });
      break;
    }
    case 'PAY_CASH': {
      const result = await placeOrder(sender, 'Delivery', state.address, 'Cash on Delivery');
      if (result.success) {
        await sendOrderConfirmation(sender, result.order_id);
      }
      break;
    }
    case 'PAY_ONLINE': {
      const result = await placeOrder(sender, 'Delivery', state.address, 'Online');
      if (result.success && result.payment_link) {
        await sendPaymentLink(sender, result.payment_link);
      }
      break;
    }
    default:
      await sendTextMessage(sender, '❓ Unknown action');
  }
}

async function handleCatalogSelection(sender, productId) {
  const product = PRODUCT_CATALOG[productId];
  if (!product) {
    await sendTextMessage(sender, '❌ Product not found');
    return;
  }
  await redisState.addToCart(sender, {
    id: productId,
    name: product.name,
    price: product.price,
    quantity: 1
  });
  const cart = await redisState.getCart(sender);
  await sendCartSummary(sender, cart);
  await redisState.setUserState(sender, { step: STATES.VIEWING_CART });
}

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
        const metadata = value.metadata || {};
        const { brandConfig, phoneNumberId, catalogId } = getBrandInfoByPhoneId(
          metadata.phone_number_id
        );
        setBrandContext(brandConfig, phoneNumberId, catalogId);
        setBrandCatalog(brandConfig);
        const state = (await redisState.getUserState(sender)) || {};

        if (type === 'interactive') {
          const iType = msg.interactive.type;
          if (iType === 'list_reply') {
            await handleListReply(sender, msg.interactive.list_reply.id, state);
          } else if (iType === 'button_reply') {
            await handleButtonReply(sender, msg.interactive.button_reply.id, state);
          } else if (iType === 'catalog_message') {
            await handleCatalogSelection(sender, msg.interactive.catalog_message.product_retailer_id);
          }
        } else if (type === 'text') {
          const text = msg.text.body.trim().toLowerCase();
          await handleText(sender, text, state);
        } else if (type === 'order') {
          const items = msg.order.product_items || [];
          for (const item of items) {
            await handleCatalogSelection(sender, item.product_retailer_id);
          }
        } else if (type === 'location') {
          const { latitude, longitude } = msg.location;
          await redisState.setLocation(sender, latitude, longitude);
          const { within, branch } = isWithinDeliveryRadius(latitude, longitude);
          if (within) {
            await redisState.setBranch(sender, branch);
            await sendTextMessage(
              sender,
              `🎉 Great news! You're near our ${branch} branch. Please send your address.`
            );
            await redisState.setUserState(sender, { step: STATES.ENTERING_ADDRESS, address: '' });
          } else {
            await sendTextMessage(sender, '🚫 Sorry, we do not deliver to your location.');
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
