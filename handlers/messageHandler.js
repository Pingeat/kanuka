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
  sendPaymentLink
} = require('../services/whatsappService');
const { placeOrder, isWithinDeliveryRadius, updateOrderStatusFromCommand } = require('../services/orderService');
const { logUserActivity } = require('../utils/csvLogger');
const { PRODUCT_CATALOG, BRANCH_COORDINATES } = require('../config/settings');
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
    await sendTextMessage(sender, `Discount set to ${value}%`);
  } else if (text === 'clear discount') {
    await redisState.clearGlobalDiscount();
    await sendTextMessage(sender, 'Discount cleared');
  } else {
    const res = await updateOrderStatusFromCommand(text);
    if (res.success) {
      await sendTextMessage(sender, 'Order status updated');
    } else {
      await sendTextMessage(sender, 'Unsupported command');
    }
  }
}

async function handleListReply(sender, id) {
  await redisState.setBranch(sender, id);
  await sendTextMessage(sender, `Branch selected: ${id}`);
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
      await sendTextMessage(sender, 'Unknown action');
  }
}

async function handleCatalogSelection(sender, productId) {
  const product = PRODUCT_CATALOG[productId];
  if (!product) {
    await sendTextMessage(sender, 'Product not found');
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
            await sendTextMessage(sender, `Nearest branch: ${branch}. Please send your address.`);
            await redisState.setUserState(sender, { step: STATES.ENTERING_ADDRESS, address: '' });
          } else {
            await sendTextMessage(sender, 'Sorry, we do not deliver to your location');
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
