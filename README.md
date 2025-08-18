# Multi-brand WhatsApp Bot

This project provides a WhatsApp bot server that can serve multiple brands.
Brand specific details such as name, bulk order contacts and product catalog
are loaded from JSON files in `config/brands`.

The active brand is selected automatically based on the WhatsApp `phone_number_id`
that receives the message. The mapping from `phone_number_id` values to brand
configurations is defined in `config/brandPhones.json`. Each entry also stores the
corresponding `catalog_id` required by the Meta API.

### Razorpay webhooks

Configure a webhook secret to validate incoming Razorpay webhooks. You can set a
global secret using `RAZORPAY_WEBHOOK_SECRET` or provide brand specific secrets
such as `RAZORPAY_WEBHOOK_SECRET_KANUKA` and
`RAZORPAY_WEBHOOK_SECRET_ZUMI`. When a webhook is received the handler looks up
the secret for the brand associated with the order and falls back to the global
secret if a brand specific one is not defined.

Two sample brands are included:

- `kanuka` mapped to `phone_number_id` `747499348442635`
- `zumi` mapped to `phone_number_id` `9876543210`

## Setup on AWS

### Install Git
```bash
sudo yum install git -y
```

### Verify installation
```bash
git --version
```

### Clone the repository
```bash
git clone https://github.com/Pingeat/TFC--Internal-bot.git
```

### Install Python 3 and pip
```bash
sudo yum install python3 python3-pip -y
python3 --version
pip3 --version
```

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Install Redis
```bash
sudo dnf install redis6
```

## Node.js Rewrite (Work in Progress)
A minimal Node.js server has been added and will gradually replace the Python backend.

### Run
```bash
node server.js
```
