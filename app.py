# app.py
import os
from flask import Flask
from handlers.webhook_handler import webhook_bp
from handlers.reminder_handler import start_scheduler
from utils.logger import get_logger

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.register_blueprint(webhook_bp)

# Initialize logger
logger = get_logger("app")

@app.route("/")
def home():
    return "Kanuka Organics Retail WhatsApp Bot is running!"

if __name__ == "__main__":
    # Start the scheduler
    # start_scheduler()
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)