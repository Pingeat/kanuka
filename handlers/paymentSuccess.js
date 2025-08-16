const { confirmOrder } = require('../services/orderService');
const { getLogger } = require('../utils/logger');
const logger = getLogger('payment_success');

async function handlePaymentSuccess(req, res) {
  const { whatsapp, order_id } = req.query;
  if (!whatsapp || !order_id) {
    res.status(400).send('Missing parameters');
    return;
  }
  try {
    await confirmOrder(whatsapp, order_id, 'Online');
    res.send('Payment confirmed');
  } catch (err) {
    logger.error(`Payment success handling failed: ${err.message}`);
    res.status(500).send('Error');
  }
}

module.exports = { handlePaymentSuccess };
