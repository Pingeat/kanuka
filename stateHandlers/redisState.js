const Redis = require('ioredis');
const { REDIS_URL } = require('../config/redis');
const { getLogger } = require('../utils/logger');

const logger = getLogger('redis_state');
const DEFAULT_BRAND = (process.env.BRAND_ID || 'default').toLowerCase();

class RedisState {
  constructor() {
    this.redis = new Redis(REDIS_URL);
    this.redis.on('error', (err) => logger.error(`Redis error: ${err}`));
  }

  _brandKey(brandId) {
    return (brandId || DEFAULT_BRAND).toLowerCase();
  }

  async getUserState(userId, brandId) {
    const b = this._brandKey(brandId);
    try {
      const data = await this.redis.get(`user:${b}:${userId}:state`);
      return data ? JSON.parse(data) : null;
    } catch (err) {
      logger.error(`getUserState error: ${err}`);
      return null;
    }
  }

  async setUserState(userId, state, brandId) {
    const b = this._brandKey(brandId);
    try {
      state.lastUpdated = new Date().toISOString();
      await this.redis.setex(
        `user:${b}:${userId}:state`,
        3600,
        JSON.stringify(state)
      );
    } catch (err) {
      logger.error(`setUserState error: ${err}`);
    }
  }

  async clearUserState(userId, brandId) {
    const b = this._brandKey(brandId);
    try {
      await this.redis.del(`user:${b}:${userId}:state`);
    } catch (err) {
      logger.error(`clearUserState error: ${err}`);
    }
  }

  async getCart(userId, brandId) {
    const b = this._brandKey(brandId);
    try {
      const data = await this.redis.get(`user:${b}:${userId}:cart`);
      const cart = data ? JSON.parse(data) : { items: [], total: 0 };
      if (!cart.items) cart.items = [];
      if (typeof cart.total !== 'number') cart.total = 0;
      return cart;
    } catch (err) {
      logger.error(`getCart error: ${err}`);
      return { items: [], total: 0 };
    }
  }

  async addToCart(userId, item, brandId) {
    const b = this._brandKey(brandId);
    // item: { id, name, price, quantity }
    const cart = await this.getCart(userId, b);

    // Check if item already exists in cart; if so, increment quantity
    const existing = cart.items.find((i) => i.id === item.id);
    if (existing) {
      existing.quantity += item.quantity;
    } else {
      cart.items.push(item);
    }

    cart.total = cart.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    cart.lastAdded = new Date().toISOString();
    cart.lastReminderDate = null;
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
    await this.redis.sadd(`cart:${b}:users`, userId);
    return cart;
  }

  async clearCart(userId, brandId) {
    const b = this._brandKey(brandId);
    try {
      await this.redis.del(`user:${b}:${userId}:cart`);
      await this.redis.srem(`cart:${b}:users`, userId);
    } catch (err) {
      logger.error(`clearCart error: ${err}`);
    }
  }

  async setLocation(userId, latitude, longitude, brandId) {
    const b = this._brandKey(brandId);
    const cart = await this.getCart(userId, b);
    cart.location = { latitude, longitude };
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
  }

  async setBranch(userId, branch, brandId) {
    const b = this._brandKey(brandId);
    const cart = await this.getCart(userId, b);
    cart.branch = branch;
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
  }

  async setPaymentMethod(userId, method, brandId) {
    const b = this._brandKey(brandId);
    const cart = await this.getCart(userId, b);
    cart.payment_method = method;
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
  }

  async setAddress(userId, address, brandId) {
    const b = this._brandKey(brandId);
    const cart = await this.getCart(userId, b);
    cart.address = address;
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
  }

  async setBrandDiscount(brandId, percent) {
    try {
      await this.redis.set(`brand:${brandId}:discount`, percent);
    } catch (err) {
      logger.error(`setBrandDiscount error: ${err}`);
    }
  }

  async getBrandDiscount(brandId) {
    try {
      const val = await this.redis.get(`brand:${brandId}:discount`);
      return val ? parseFloat(val) : null;
    } catch (err) {
      logger.error(`getBrandDiscount error: ${err}`);
      return null;
    }
  }

  async clearBrandDiscount(brandId) {
    try {
      await this.redis.del(`brand:${brandId}:discount`);
    } catch (err) {
      logger.error(`clearBrandDiscount error: ${err}`);
    }
  }

  async createOrder(order) {
    await this.redis.rpush('orders:all', JSON.stringify(order));
    await this.redis.setex(`order:${order.order_id}:active`, 604800, '1');
  }

  async archiveOrder(order) {
    try {
      await this.redis.rpush('orders:archive', JSON.stringify(order));
    } catch (err) {
      logger.error(`archiveOrder error: ${err}`);
    }
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
    const all = await this.redis.lrange('orders:all', 0, -1);
    let order = null;
    let orderJson = null;
    for (const str of all) {
      const o = JSON.parse(str);
      if (o.order_id === orderId) {
        order = o;
        orderJson = str;
        break;
      }
    }
    if (!order) return false;
    order.status = status;
    await this.redis.lrem('orders:all', 0, orderJson);
    await this.redis.rpush('orders:all', JSON.stringify(order));
    return true;
  }

  async getUsersWithCarts(brandId) {
    const b = this._brandKey(brandId);
    try {
      return await this.redis.smembers(`cart:${b}:users`);
    } catch (err) {
      logger.error(`getUsersWithCarts error: ${err}`);
      return [];
    }
  }

  async markCartReminderSent(userId, dateStr, brandId) {
    const b = this._brandKey(brandId);
    const cart = await this.getCart(userId, b);
    cart.lastReminderDate = dateStr;
    await this.redis.setex(
      `user:${b}:${userId}:cart`,
      86400,
      JSON.stringify(cart)
    );
  }

  async pushReminder(reminder) {
    try {
      await this.redis.rpush('reminders:queue', JSON.stringify(reminder));
    } catch (err) {
      logger.error(`pushReminder error: ${err}`);
    }
  }

  async popReminder() {
    try {
      const data = await this.redis.lpop('reminders:queue');
      return data ? JSON.parse(data) : null;
    } catch (err) {
      logger.error(`popReminder error: ${err}`);
      return null;
    }
  }
}

module.exports = new RedisState();
