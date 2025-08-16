const fs = require('fs');
const path = require('path');
const { getLogger } = require('../utils/logger');

const logger = getLogger('brand_service');

function loadBrandConfig(brand) {
  try {
    const file = path.join(__dirname, '..', 'config', 'brands', `${brand}.json`);
    const data = fs.readFileSync(file, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    logger.error(`loadBrandConfig error: ${err}`);
    return null;
  }
}

module.exports = { loadBrandConfig };
