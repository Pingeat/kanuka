const { BRANCH_COORDINATES, DELIVERY_RADIUS_KM, ORDER_STATUS, PRODUCT_CATALOG } = require('../config/settings');
const redisState = require('../stateHandlers/redisState');
const { getLogger } = require('../utils/logger');
const logger = getLogger('order_service');

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

async function placeOrder(userId, deliveryType, address = null, paymentMethod = 'Cash on Delivery') {
  const cart = await redisState.getCart(userId);
  if (!cart.items.length) {
    return { success: false, message: 'Cart is empty' };
  }
  const orderId = generateOrderId();
  const order = {
    order_id: orderId,
    user_id: userId,
    items: cart.items,
    total: cart.total,
    status: paymentMethod === 'Cash on Delivery' ? ORDER_STATUS.PAID : ORDER_STATUS.PENDING,
    delivery_type: deliveryType,
    delivery_address: address,
    payment_method: paymentMethod,
    order_date: new Date().toISOString()
  };
  await redisState.createOrder(order);
  await redisState.clearCart(userId);
  return { success: true, order_id: orderId };
}

async function processPayment(userId, orderId) {
  logger.info(`Processing payment for ${userId} and order ${orderId}`);
  // Real implementation would integrate with payment gateway
  return { success: true };
}

async function updateOrderStatusFromCommand(command) {
  const lower = command.toLowerCase();
  let status = null;
  if (lower.includes('ready')) status = ORDER_STATUS.READY;
  else if (lower.includes('ontheway') || lower.includes('on the way')) status = ORDER_STATUS.ON_THE_WAY;
  else if (lower.includes('delivered')) status = ORDER_STATUS.DELIVERED;
  const parts = lower.split(/\s+/);
  const orderId = parts[parts.length - 1].toUpperCase();
  if (!status || !orderId) return { success: false, message: 'Invalid command' };
  const ok = await redisState.updateOrderStatus(orderId, status);
  return { success: ok };
}

async function confirmOrder(whatsappNumber, orderId, paymentMethod) {
  logger.info(`Confirming order ${orderId} for ${whatsappNumber}`);
  // Lookup pending order if needed and finalize
  const success = true; // placeholder
  return { success };
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
