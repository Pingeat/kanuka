# # handlers/webhook_handler.py
# import json
# from flask import request
# from config.credentials import Credentials
# from services.order_service import OrderService
# from utils.logger import get_logger

# logger = get_logger("webhook_handler")

# class WebhookHandler:
#     def __init__(self, redis_state, whatsapp_service, order_service, message_handler=None):
#         self.redis = redis_state
#         self.whatsapp = whatsapp_service
#         self.order_service = order_service
#         self.message_handler = message_handler
#         if not self.message_handler:
#             from handlers.message_handler import MessageHandler
#             self.message_handler = MessageHandler(
#                 redis_state, 
#                 whatsapp_service, 
#                 order_service,
#                 None  # Brand service will be initialized properly in app.py
#             )
    
#     def verify(self):
#         """Verify WhatsApp webhook"""
#         mode = request.args.get("hub.mode")
#         token = request.args.get("hub.verify_token")
#         challenge = request.args.get("hub.challenge")
        
#         if mode == "subscribe" and token == Credentials.VERIFY_TOKEN:
#             return challenge, 200
#         return "Verification token mismatch", 403
    
#     def handle_webhook(self):
#         """Process incoming webhook events"""
#         body = request.get_json()
#         logger.info(f"Received webhook: {json.dumps(body)}")
        
#         # Process WhatsApp messages
#         if body.get("object") == "whatsapp_business_account":
#             for entry in body["entry"]:
#                 for change in entry["changes"]:
#                     value = change["value"]
                    
#                     if "messages" in value:
#                         for message in value["messages"]:
#                             phone = message["from"]
#                             msg_type = message["type"]
                            
#                             if msg_type == "text":
#                                 text = message["text"]["body"]
#                                 self._process_text_message(phone, text)
#                             elif msg_type == "interactive":
#                                 # Handle button responses
#                                 interactive = message["interactive"]
#                                 if interactive["type"] == "button_reply":
#                                     self._process_button_reply(
#                                         phone, 
#                                         interactive["button_reply"]["id"]
#                                     )
#                                 elif interactive["type"] == "list_reply":
#                                     self._process_list_reply(
#                                         phone,
#                                         interactive["list_reply"]["id"]
#                                     )
#                             elif msg_type == "location":
#                                 # Handle location sharing
#                                 location = message["location"]
#                                 self._process_location(
#                                     phone,
#                                     location["latitude"],
#                                     location["longitude"],
#                                     location.get("name", "Shared Location")
#                                 )
        
#         # Process Razorpay webhooks
#         elif "razorpay" in str(body).lower():  # Simplified check
#             self._handle_razorpay_webhook(body)
        
#         return "OK", 200
    
#     def _process_text_message(self, phone: str, text: str):
#         """Process text messages from users"""
#         logger.info(f"Processing text message from {phone}: {text}")
#         # In production: normalize text and handle commands
#         text = text.strip().lower()
        
#         # Handle order status commands (admin only)
#         if phone == Credentials.ADMIN_PHONE:
#             if text.startswith("ready ") or text.startswith("on the way ") or text.startswith("delivered "):
#                 parts = text.split(maxsplit=1)
#                 status = parts[0].replace("on the way", "ontheway")
#                 order_id = parts[1].upper()
#                 self.order_service.update_order_status(order_id, status)
#                 return
        
#         # Forward to message handler
#         self.message_handler.handle_message(phone, text, "text")
    
#     def _process_button_reply(self, phone: str, button_id: str):
#         """Process button reply interactions"""
#         logger.info(f"Processing button reply from {phone}: {button_id}")
#         self.message_handler.handle_message(phone, button_id, "button")
    
#     def _process_list_reply(self, phone: str, list_id: str):
#         """Process catalog list selections"""
#         logger.info(f"Processing list reply from {phone}: {list_id}")
#         self.message_handler.handle_message(phone, list_id, "interactive")
    
#     def _process_location(self, phone: str, lat: float, long: float, name: str):
#         """Process shared location"""
#         logger.info(f"Processing location from {phone}: {lat}, {long} ({name})")
#         # In a real implementation, you'd calculate distance to branches here
#         # For now, we'll just use the area name as the location
#         self.message_handler.handle_message(phone, name, "location")
    
#     def _handle_razorpay_webhook(self, payload: dict):
#         """Process Razorpay payment webhooks"""
#         logger.info(f"Processing Razorpay webhook: {json.dumps(payload)}")
#         if payload.get("event") == "payment.captured":
#             try:
#                 order_id = payload["payload"]["payment"]["entity"]["order_id"]
#                 self.order_service.handle_payment_success(order_id)
#             except KeyError as e:
#                 logger.error(f"Invalid Razorpay webhook payload: {str(e)}")










# # handlers/webhook_handler.py
# from flask import Blueprint, request, jsonify
# from handlers.message_handler import handle_incoming_message
# from services.order_service import confirm_order
# from services.whatsapp_service import send_text_message
# from config.credentials import META_VERIFY_TOKEN
# from utils.logger import get_logger
# from handlers.reminder_handler import start_scheduler

# logger = get_logger("webhook_handler")

# webhook_bp = Blueprint('webhook', __name__)

# @webhook_bp.route("/webhook", methods=["POST"])
# def webhook():
#     """Handle incoming webhook POST requests"""
#     logger.info("Incoming POST request received.")
#     data = request.get_json()
#     logger.debug(f"Data received: {data}")
    
#     # Process the incoming message
#     status, code = handle_incoming_message(data)
#     return jsonify({"status": status}), code

# @webhook_bp.route("/webhook", methods=["GET"])
# def verify_webhook():
#     """Verify webhook with Meta"""
#     logger.info("Verifying token...")
#     hub_mode = request.args.get("hub.mode")
#     hub_token = request.args.get("hub.verify_token")
#     hub_challenge = request.args.get("hub.challenge")
    
#     if hub_mode == "subscribe" and hub_token == META_VERIFY_TOKEN:
#         logger.info("Verification successful.")
#         return hub_challenge, 200
#     else:
#         logger.warning("Verification failed.")
#         return "Verification failed", 403

# # Payment success webhook
# @webhook_bp.route("/payment-success", methods=["GET"])
# def payment_success():
#     """Handle payment success callback"""
#     logger.info("Payment success callback received.")
#     whatsapp_number = request.args.get("whatsapp")
#     order_id = request.args.get("order_id")
    
#     if whatsapp_number and order_id:
#         # Confirm the order with payment method
#         confirm_order(whatsapp_number, order_id, "Pay Now")
#         return "Payment confirmed", 200
#     else:
#         logger.error("Missing parameters in payment success callback")
#         return "Missing parameters", 400

# # Razorpay webhook (for production)
# @webhook_bp.route("/razorpay-webhook", methods=["POST"])
# def razorpay_webhook():
#     """Handle Razorpay payment webhook"""
#     logger.info("Razorpay webhook received.")
#     data = request.get_json()
    
#     if data.get("event") == "payment_link.paid":
#         payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
#         whatsapp_number = payment_data.get("customer", {}).get("contact")
#         order_id = payment_data.get("reference_id")
        
#         if whatsapp_number and order_id:
#             send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
#             # Confirm the order
#             confirm_order(whatsapp_number, order_id, "Pay Now")
    
#     return "OK", 200






# handlers/webhook_handler.py
import json
from flask import Blueprint, request, jsonify
from handlers.message_handler import handle_incoming_message
from services.order_service import confirm_order
from services.whatsapp_service import send_text_message
from config.credentials import META_VERIFY_TOKEN
from stateHandlers import redis_state
from utils.logger import get_logger
from handlers.reminder_handler import start_scheduler

logger = get_logger("webhook_handler")

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming webhook POST requests"""
    logger.info("Incoming POST request received.")
    data = request.get_json()
    logger.debug(f"Data received: {data}")
    
    # Process the incoming message
    status, code = handle_incoming_message(data)
    return jsonify({"status": status}), code

@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verify webhook with Meta"""
    logger.info("Verifying token...")
    hub_mode = request.args.get("hub.mode")
    hub_token = request.args.get("hub.verify_token")
    hub_challenge = request.args.get("hub.challenge")
    
    if hub_mode == "subscribe" and hub_token == META_VERIFY_TOKEN:
        logger.info("Verification successful.")
        return hub_challenge, 200
    else:
        logger.warning("Verification failed.")
        return "Verification failed", 403


# # Razorpay webhook (for production)
# @webhook_bp.route("/razorpay-webhook-kanuka", methods=["POST"])
# def razorpay_webhook():
#     """Handle Razorpay payment webhook"""
#     logger.info("Razorpay webhook received.")
#     data = request.get_json()
    
#     if data.get("event") == "payment_link.paid":
#         payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
#         whatsapp_number = payment_data.get("customer", {}).get("contact")
#         order_id = payment_data.get("reference_id")
        
#         if whatsapp_number and order_id:
#             send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
#             # Confirm the order
#             confirm_order(whatsapp_number, order_id, "Pay Now")
    
#     return "OK", 200


# Razorpay webhook (for production)
# @webhook_bp.route("/razorpay-webhook-kanuka", methods=["POST"])
# def razorpay_webhook():
#     """Handle Razorpay payment webhook"""
#     logger.info("Razorpay webhook received.")
#     data = request.get_json()
    
#     if data.get("event") == "payment_link.paid":
#         payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
#         whatsapp_number = payment_data.get("customer", {}).get("contact")
#         order_id = payment_data.get("reference_id")
        
#         if whatsapp_number and order_id:
#             send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
#             # Confirm the order
#             confirm_order(whatsapp_number, order_id, "online")
    
#     return "OK", 200




@webhook_bp.route("/razorpay-webhook-kanuka", methods=["POST"])
def razorpay_webhook():
    """Handle Razorpay payment webhook"""
    logger.info("Razorpay webhook received.")
    data = request.get_json()
    
    if data.get("event") == "payment_link.paid":
        payment_data = data.get("payload", {}).get("payment_link", {}).get("entity", {})
        whatsapp_number = payment_data.get("customer", {}).get("contact")
        order_id = payment_data.get("reference_id")
        
        if whatsapp_number and order_id:
            send_text_message(whatsapp_number, "✅ Your payment is confirmed! Your order is being processed.")
            # Confirm the order with correct payment method string
            confirm_order(whatsapp_number, order_id, "Pay Now")
    
    return "OK", 200