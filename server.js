require('dotenv').config();
const express = require('express');
const path = require('path');
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

// Serve static assets for chat interface
app.use(express.static(path.join(__dirname, 'public')));

// Basic route to serve the chat page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/webhook', verifyWebhook);
app.post('/webhook', handleWebhook);
app.get('/payment-success', handlePaymentSuccess);
app.post('/payment-made', handlePaymentWebhook);

// Simple endpoint to echo chat messages
app.post('/message', (req, res) => {
  const { message } = req.body || {};
  res.json({ reply: `Echo: ${message || ''}` });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server listening on ${PORT}`);
});

startCartReminderScheduler();
startReminderScheduler();
