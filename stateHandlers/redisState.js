const Redis = require('ioredis');
const { REDIS_URL } = require('../config/redis');
const { getLogger } = require('../utils/logger');

const logger = getLogger('redis_state');

class RedisState {
  constructor() {
    this.redis = new Redis(REDIS_URL);
    this.redis.on('error', (err) => logger.error(`Redis error: ${err}`));
  }

  async getUserState(userId) {
    try {
      const data = await this.redis.get(`user:${userId}:state`);
      return data ? JSON.parse(data) : null;
    } catch (err) {
      logger.error(`getUserState error: ${err}`);
      return null;
    }
  }

  async setUserState(userId, state) {
    try {
      state.lastUpdated = new Date().toISOString();
      await this.redis.setex(`user:${userId}:state`, 3600, JSON.stringify(state));
    } catch (err) {
      logger.error(`setUserState error: ${err}`);
    }
  }

  async clearUserState(userId) {
    try {
      await this.redis.del(`user:${userId}:state`);
    } catch (err) {
      logger.error(`clearUserState error: ${err}`);
    }
  }

  async getCart(userId) {
    try {
      const data = await this.redis.get(`user:${userId}:cart`);
      const cart = data ? JSON.parse(data) : { items: [], total: 0 };
      if (!cart.items) cart.items = [];
      if (typeof cart.total !== 'number') cart.total = 0;
      return cart;
    } catch (err) {
      logger.error(`getCart error: ${err}`);
      return { items: [], total: 0 };
    }
  }

  async addToCart(userId, item) {
    // item: { id, name, price, quantity }
    const cart = await this.getCart(userId);
    cart.items.push(item);
    cart.total = cart.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    cart.lastAdded = new Date().toISOString();
    cart.lastReminderDate = null;
    await this.redis.setex(`user:${userId}:cart`, 86400, JSON.stringify(cart));
    await this.redis.sadd('cart:users', userId);
    return cart;
  }

  async clearCart(userId) {
    try {
      await this.redis.del(`user:${userId}:cart`);
      await this.redis.srem('cart:users', userId);
    } catch (err) {
      logger.error(`clearCart error: ${err}`);
    }
  }

  async setLocation(userId, latitude, longitude) {
    const cart = await this.getCart(userId);
    cart.location = { latitude, longitude };
    await this.redis.setex(`user:${userId}:cart`, 86400, JSON.stringify(cart));
  }

  async setBranch(userId, branch) {
    const cart = await this.getCart(userId);
    cart.branch = branch;
    await this.redis.setex(`user:${userId}:cart`, 86400, JSON.stringify(cart));
  }

  async setPaymentMethod(userId, method) {
    const cart = await this.getCart(userId);
    cart.payment_method = method;
    await this.redis.setex(`user:${userId}:cart`, 86400, JSON.stringify(cart));
  }

  async createOrder(order) {
    await this.redis.rpush('orders:all', JSON.stringify(order));
    await this.redis.setex(`order:${order.order_id}:active`, 604800, '1');
  }

  async getOrder(orderId) {
    const all = await this.redis.lrange('orders:all', 0, -1);
    for (const str of all) {
      const o = JSON.parse(str);
      if (o.order_id === orderId) return o;
    }
    return null;
  }

  async updateOrderStatus(orderId, status) {
    const order = await this.getOrder(orderId);
    if (!order) return false;
    order.status = status;
    await this.redis.rpush('orders:all', JSON.stringify(order));
    return true;
  }

  async getUsersWithCarts() {
    try {
      return await this.redis.smembers('cart:users');
    } catch (err) {
      logger.error(`getUsersWithCarts error: ${err}`);
      return [];
    }
  }

  async markCartReminderSent(userId, dateStr) {
    const cart = await this.getCart(userId);
    cart.lastReminderDate = dateStr;
    await this.redis.setex(`user:${userId}:cart`, 86400, JSON.stringify(cart));
  }
}

module.exports = new RedisState();
