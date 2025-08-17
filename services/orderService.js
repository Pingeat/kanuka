const {
  BRANCH_COORDINATES,
  DELIVERY_RADIUS_KM,
  ORDER_STATUS,
  PRODUCT_CATALOG,
  setBrandCatalog
} = require('../config/settings');
const { getLogger } = require('../utils/logger');
const { generateRazorpayLink } = require('../utils/paymentUtils');
const { loadBrandConfig } = require('./brandService');
const logger = getLogger('order_service');

let redisState = null;
function getRedisState() {
  if (!redisState) {
    redisState = require('../stateHandlers/redisState');
  }
  return redisState;
}

function generateOrderId() {
  return `ORD${Date.now().toString(36).toUpperCase()}`;
}

function toRad(v) {
  return (v * Math.PI) / 180;
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function findNearestBranch(lat, lon) {
  let nearest = null;
  let min = Infinity;
  for (const [branch, coords] of Object.entries(BRANCH_COORDINATES)) {
    const d = calculateDistance(lat, lon, coords[0], coords[1]);
    if (d < min) {
      min = d;
      nearest = branch;
    }
  }
  return { branch: nearest, distance: min };
}

function isWithinDeliveryRadius(lat, lon) {
  const { branch, distance } = findNearestBranch(lat, lon);
  return { within: distance <= DELIVERY_RADIUS_KM, branch, distance };
}

async function placeOrder(
  userId,
  deliveryType,
  address = null,
  paymentMethod = 'Cash on Delivery',
  brandId
) {
  const cart = await getRedisState().getCart(userId, brandId);
  if (!cart.items.length) {
    return { success: false, message: 'Cart is empty' };
  }

  if (deliveryType === 'Delivery' && cart.location) {
    const { within, branch } = isWithinDeliveryRadius(cart.location.latitude, cart.location.longitude);
    if (!within) {
      return { success: false, message: 'Outside delivery radius' };
    }
    cart.branch = branch;
  }

  const discount = brandId ? await getRedisState().getBrandDiscount(brandId) : null;
  const actualTotal = cart.items.reduce(
    (sum, i) => sum + i.price * i.quantity,
    0
  );
  const discountAmount = discount ? (actualTotal * discount) / 100 : 0;
  const total = actualTotal - discountAmount;

  const orderId = generateOrderId();
  const order = {
    order_id: orderId,
    user_id: userId,
    items: cart.items,
    actual_total: actualTotal,
    discount_percentage: discount || 0,
    discount_amount: discountAmount,
    total,
    status:
      paymentMethod === 'Cash on Delivery'
        ? ORDER_STATUS.PAID
        : ORDER_STATUS.PENDING,
    delivery_type: deliveryType,
    delivery_address: address || cart.address,
    payment_method: paymentMethod,
    branch: cart.branch,
    brand_id: brandId,
    order_date: new Date().toISOString()
  };

  if (paymentMethod !== 'Cash on Delivery') {
    order.payment_link = await generateRazorpayLink(total, orderId, userId);
  }

  await getRedisState().createOrder(order);

  if (order.branch && paymentMethod === 'Cash on Delivery') {
    const { sendOrderAlert } = require('./whatsappService');
    try {
      await sendOrderAlert(
        order.branch,
        orderId,
        order.items,
        order.total,
        userId,
        order.delivery_address,
        deliveryType,
        paymentMethod,
        order.discount_percentage,
        order.discount_amount
      );
    } catch (err) {
      logger.error(`Failed to send order alert: ${err.message}`);
    }
  }

  await getRedisState().clearCart(userId, brandId);
  return { success: true, order_id: orderId, payment_link: order.payment_link };
}

async function processPayment(userId, orderId) {
  logger.info(`Processing payment for ${userId} and order ${orderId}`);
  const order = await getRedisState().getOrder(orderId);
  if (!order) {
    return { success: false, message: 'Order not found' };
  }
  try {
    const link = await generateRazorpayLink(order.total, orderId, userId);
    order.payment_link = link;
    return { success: true, payment_link: link };
  } catch (err) {
    logger.error(`Payment processing failed: ${err.message}`);
    return { success: false, message: 'Payment processing failed' };
  }
}

async function updateOrderStatusFromCommand(command) {
  const lower = command.toLowerCase();
  let status = null;
  if (lower.includes('ready')) status = ORDER_STATUS.READY;
  else if (lower.includes('ontheway') || lower.includes('on the way'))
    status = ORDER_STATUS.ON_THE_WAY;
  else if (lower.includes('delivered')) status = ORDER_STATUS.DELIVERED;
  const parts = lower.split(/\s+/);
  const orderId = parts[parts.length - 1].toUpperCase();
  if (!status || !orderId) return { success: false, message: 'Invalid command' };
  const order = await getRedisState().getOrder(orderId);
  if (!order) return { success: false, message: 'Order not found' };
  const ok = await getRedisState().updateOrderStatus(orderId, status);
  if (!ok) return { success: false, message: 'Update failed' };
  const { sendOrderStatusUpdate } = require('./whatsappService');
  await sendOrderStatusUpdate(order.user_id, orderId, status);
  if (status === ORDER_STATUS.DELIVERED) {
    await getRedisState().archiveOrder(order);
  }
  return { success: true, message: `Order ${orderId} status updated` };
}

async function confirmOrder(whatsappNumber, orderId, paymentMethod = 'Online') {
  logger.info(`Confirming order ${orderId} for ${whatsappNumber}`);
  const order = await getRedisState().getOrder(orderId);
  if (!order) return { success: false };
  const { sendOrderAlert, sendOrderConfirmation, setBrandContext } = require('./whatsappService');
  const brandId = order.brand_id || 'kanuka';
  const brandConfig = loadBrandConfig(brandId) || {};
  const upper = brandId.toUpperCase();
  const phoneId = process.env[`META_PHONE_NUMBER_ID_${upper}`];
  const catalogId = process.env[`CATALOG_ID_${upper}`];
  const accessToken = process.env[`META_ACCESS_TOKEN_${upper}`];
  setBrandContext(brandConfig, phoneId, catalogId, accessToken);
  setBrandCatalog(brandConfig);

  await getRedisState().updateOrderStatus(orderId, ORDER_STATUS.PAID);
  if (order.branch) {
    await sendOrderAlert(
      order.branch,
      orderId,
      order.items,
      order.total,
      whatsappNumber,
      order.delivery_address,
      order.delivery_type,
      paymentMethod,
      order.discount_percentage,
      order.discount_amount
    );
  }
  await sendOrderConfirmation(whatsappNumber, orderId);
  return { success: true };
}

module.exports = {
  generateOrderId,
  findNearestBranch,
  isWithinDeliveryRadius,
  placeOrder,
  processPayment,
  updateOrderStatusFromCommand,
  confirmOrder
};
