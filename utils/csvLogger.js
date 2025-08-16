const fs = require('fs');
const path = require('path');
const { getLogger } = require('./logger');

const logger = getLogger('csv_logger');
const logDir = path.join(__dirname, '..', 'logs');
const logFile = path.join(logDir, 'user_activity.csv');

function logUserActivity(user, action, details = '') {
  try {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    const line = `${new Date().toISOString()},${user},${action},${details.replace(/,/g, ';')}`;
    fs.appendFileSync(logFile, line + '\n');
  } catch (err) {
    logger.error(`logUserActivity error: ${err}`);
  }
}

module.exports = { logUserActivity };
