const { handleIncomingMessage } = require('./messageHandler');
const { getLogger } = require('../utils/logger');
const logger = getLogger('webhook_handler');

async function handleWebhook(req, res) {
  logger.info('Webhook POST received');
  const result = await handleIncomingMessage(req.body || {});
  res.status(200).json(result);
}

function verifyWebhook(req, res) {
  const verifyToken = process.env.META_VERIFY_TOKEN || 'verify';
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];
  if (mode === 'subscribe' && token === verifyToken) {
    res.status(200).send(challenge);
  } else {
    res.sendStatus(403);
  }
}

module.exports = { handleWebhook, verifyWebhook };
