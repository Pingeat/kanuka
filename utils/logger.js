function getLogger(name) {
  return {
    info: (msg) => console.log(`[${name}] ${msg}`),
    error: (msg) => console.error(`[${name}] ${msg}`),
    debug: (msg) => console.debug(`[${name}] ${msg}`)
  };
}

module.exports = { getLogger };
