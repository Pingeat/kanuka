function formatMessage(level, name, msg) {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${name}] ${level.toUpperCase()}: ${msg}`;
}

function getLogger(name) {
  return {
    info: (msg) => console.log(formatMessage('info', name, msg)),
    error: (msg) => console.error(formatMessage('error', name, msg)),
    debug: (msg) => console.debug(formatMessage('debug', name, msg)),
  };
}

module.exports = { getLogger };
