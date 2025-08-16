require('dotenv').config();
const express = require('express');
const { handleWebhook, verifyWebhook } = require('./handlers/webhookHandler');
const { handlePaymentSuccess } = require('./handlers/paymentSuccess');
const { handlePaymentWebhook } = require('./handlers/paymentWebhook');
const { startCartReminderScheduler } = require('./schedulers/cartReminder');
const { startReminderScheduler } = require('./schedulers/reminderScheduler');
const { getLogger } = require('./utils/logger');

const logger = getLogger('server');

const app = express();
app.use(
  express.json({
    verify: (req, res, buf) => {
      // Store the raw request body for Razorpay signature verification
      req.rawBody = buf.toString();
    }
  })
);

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/webhook', verifyWebhook);
app.post('/webhook', handleWebhook);
app.get('/payment-success', handlePaymentSuccess);
app.post('/payment-made', handlePaymentWebhook);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server listening on ${PORT}`);
});

startCartReminderScheduler();
startReminderScheduler();
