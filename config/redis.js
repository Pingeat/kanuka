require('dotenv').config();

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';

module.exports = { REDIS_URL };
