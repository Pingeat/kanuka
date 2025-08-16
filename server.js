const express = require('express');
const { handleWebhook, verifyWebhook } = require('./handlers/webhookHandler');
const { startCartReminderScheduler } = require('./schedulers/cartReminder');
const { startReminderScheduler } = require('./schedulers/reminderScheduler');

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/webhook', verifyWebhook);
app.post('/webhook', handleWebhook);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server listening on ${PORT}`);
});

startCartReminderScheduler();
startReminderScheduler();
