# services/whatsapp_service.py
import requests
import json
from config.credentials import META_ACCESS_TOKEN, WHATSAPP_API_URL, WHATSAPP_CATALOG_ID
from config.settings import BRANCH_COORDINATES, BRAND_NAME, GREETING_MESSAGE, ORDER_STATUS, PRODUCT_CATALOG
from utils.logger import get_logger
from stateHandlers.redis_state import redis_state
from utils.payment_utils import generate_payment_link

logger = get_logger("whatsapp_service")

def send_text_message(to, message):
    """Send a text message via WhatsApp"""
    logger.info(f"Sending message to {to}")
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"WhatsApp API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"WhatsApp API error: {response.text}")
        
        return response
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return None

def send_main_menu(to):
    """Send main menu with interactive buttons"""
    logger.info(f"Sending main menu to {to}")
    
    message = GREETING_MESSAGE
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "ORDER_NOW",
                            "title": "🛍️ Order Now"
                        }
                    },
                    # {
                    #     "type": "reply",
                    #     "reply": {
                    #         "id": "BULK_ORDERS",
                    #         "title": "📦 Bulk Orders"
                    #     }
                    # }
                ]
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Main menu sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Main menu error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send main menu: {str(e)}")
        return None

def send_catalog(to):
    """Send catalog message using WhatsApp Catalog"""
    logger.info(f"Sending catalog to {to}")
    
    message = "🌟 *EXPLORE OUR PRODUCTS*\n\n" \
             "Browse our catalog and select items to add to your cart.\n\n" \
             "Tap the button below to view our catalog:"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "catalog_message",
            "body": {
                "text": message
            },
            "action": {
                "name": "catalog_message",
                "catalog_id": WHATSAPP_CATALOG_ID
            }
        }
    }
    
    # Only include catalog_id if we have one configured
    # if WHATSAPP_CATALOG_ID:
    #     payload["interactive"]["action"]["catalog_id"] = WHATSAPP_CATALOG_ID
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Catalog template sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Catalog error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send catalog: {str(e)}")
        return None

def send_cart_summary(to):
    """Send cart summary to user with interactive buttons"""
    logger.info(f"Sending cart summary to {to}")
    cart = redis_state.get_cart(to)
    if not cart["items"]:
        message = "🛒 *YOUR CART IS EMPTY*\n\n"
        message += "Browse our catalog to add items to your cart."
        return send_text_message(to, message)
    
    message = "🛒 *YOUR CART*\n\n"
    total = 0
    
    for item in cart["items"]:
        item_total = item["quantity"] * item["price"]
        total += item_total
        message += f"• {item['name']} x{item['quantity']} = ₹{item_total}\n"
    
    message += f"\n*TOTAL*: ₹{total}\n\n"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "CONTINUE_SHOPPING",
                            "title": "🛍️ Continue"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "PROCEED_TO_CHECKOUT",
                            "title": "✅ Checkout"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "CLEAR_CART",
                            "title": "🗑️ Clear Cart"
                        }
                    }
                ]
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Cart summary template sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Cart summary error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send cart summary: {str(e)}")
        return None

def send_delivery_options(to):
    """Send delivery options to user with interactive buttons"""
    logger.info(f"Sending delivery options to {to}")
    
    message = "📍 *DELIVERY OPTIONS*\n\n" \
             "How would you like to receive your order?"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "DELIVERY",
                            "title": "🚚 Home Delivery"
                        }
                    },
                    # {
                    #     "type": "reply",
                    #     "reply": {
                    #         "id": "TAKEAWAY",
                    #         "title": "🏪 Store Pickup"
                    #     }
                    # }
                ]
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Delivery options sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Delivery options error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send delivery options: {str(e)}")
        return None

def send_location_request(to):
    """Send location request message"""
    logger.info(f"Sending location request to {to}")
    
    message = "📍 *SHARE YOUR LOCATION*\n\n" \
             "Please share your current location so we can check if we deliver to your area.\n\n" \
             "We deliver within 4km radius of our branches."
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Location request sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Location request error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send location request: {str(e)}")
        return None

def send_branch_selection(to):
    """Send branch selection menu with interactive list"""
    logger.info(f"Sending branch selection to {to}")
    
    # Create sections for the list
    sections = [{
        "title": "Select Branch",
        "rows": [
            {"id": branch, "title": branch, "description": ""} 
            for branch in BRANCH_COORDINATES.keys()
        ]
    }]
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🏪 SELECT A BRANCH"
            },
            "body": {
                "text": "Please select a branch for pickup:"
            },
            "footer": {
                "text": "Tap to select your preferred branch"
            },
            "action": {
                "button": "Select Branch",
                "sections": sections
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Branch selection template sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Branch selection error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send branch selection: {str(e)}")
        return None

def send_payment_options(to):
    """Send payment options to user with interactive buttons"""
    logger.info(f"Sending payment options to {to}")
    
    message = "💳 *PAYMENT OPTIONS*\n\n" \
             "How would you like to pay for your order?"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "PAY_NOW",
                            "title": "💳 Pay Now"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "CASH_ON_DELIVERY",
                            "title": "💵 Cash on Delivery"
                        }
                    }
                ]
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Payment options sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Payment options error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send payment options: {str(e)}")
        return None

def send_bulk_order_info(to):
    """Send bulk order contact information"""
    logger.info(f"Sending bulk order info to {to}")
    
    from config.settings import BULK_ORDER_CONTACT
    
    message = "📞 *BULK ORDER INFORMATION*\n\n" \
             "For bulk orders (more than 10 items), please contact us directly:\n\n" \
             f"📱 Phone: {BULK_ORDER_CONTACT['phone']}\n" \
             f"✉️ Email: {BULK_ORDER_CONTACT['email']}\n\n" \
             "Our sales team will assist you with special pricing and delivery options."
    
    return send_text_message(to, message)

def send_order_confirmation(to, order_id, branch, items, total, payment_method):
    """Send order confirmation message with detailed order items"""
    logger.info(f"Sending order confirmation to {to} for order {order_id}")
    
    message = f"✅ *ORDER CONFIRMED*\n\n" \
             f"Order ID: #{order_id}\n" \
             f"Branch: {branch}\n" \
             f"Payment Method: {payment_method}\n\n" \
             "ORDER ITEMS:\n"
    
    for item in items:
        item_total = item["quantity"] * item["price"]
        message += f"• {item['name']} x{item['quantity']} = ₹{item_total}\n"
    
    message += f"\n*TOTAL*: ₹{total}\n\n"
    
    if payment_method == "Pay Now":
        message += "Please wait while we generate your payment link..."
    else:
        message += "Your order will be processed shortly. Thank you for shopping with Kanuka Organics!"
    
    return send_text_message(to, message)

def send_payment_processing(to):
    """Send payment processing message"""
    logger.info(f"Sending payment processing message to {to}")
    
    message = "🔄 *GENERATING PAYMENT LINK*\n\n" \
             "Please wait a moment while we create your secure payment link..."
    
    return send_text_message(to, message)

def send_payment_link(to, order_id, amount):
    """Send payment link for online payment"""
    logger.info(f"Sending payment link to {to} for order {order_id}")
    
    # In a real implementation, this would generate a Razorpay payment link
    payment_link = generate_payment_link(to,1,order_id)
    
    message = "💳 *SECURE PAYMENT*\n\n" \
             f"Please complete payment for your order #{order_id}:\n\n" \
             f"Amount: ₹{amount}\n\n" \
             f"Payment Link: {payment_link}\n\n" \
             "You will receive order confirmation after payment is successful."
    
    return send_text_message(to, message)


def send_order_status_update(to, order_id, status):
    """Send order status update to customer"""
    logger.info(f"Sending order status update to {to} for order {order_id}")
    
    message = f"🔄 *ORDER STATUS UPDATE*\n\n" \
             f"Order ID: #{order_id}\n" \
             f"Status: {status}\n\n"
    
    if status == ORDER_STATUS["READY"]:
        message += "Your order is ready for delivery/pickup."
    elif status == ORDER_STATUS["ON_THE_WAY"]:
        message += "Your order is on the way to you. 🚚"
    elif status == ORDER_STATUS["DELIVERED"]:
        message += "Your order has been delivered. Thank you for shopping with us! ❤️"
    
    return send_text_message(to, message)

def send_cart_reminder(to, order_id):
    """Send cart reminder with order now button"""
    logger.info(f"Sending cart reminder to {to} for order {order_id}")
    
    cart = redis_state.get_cart(to)
    
    message = "⏰ *CART REMINDER*\n\n" \
             "You have items in your cart. Would you like to complete your order?\n\n"
    
    # Add cart items
    for item in cart["items"]:
        message += f"• {item['name']} x{item['quantity']}\n"
    
    message += f"\n*TOTAL*: ₹{cart['total']}\n\n" \
             "Tap the button below to proceed with your order:"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"ORDER_NOW:{order_id}",
                            "title": "🛍️ Order Now"
                        }
                    }
                ]
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        logger.info(f"Cart reminder sent. Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Cart reminder error: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Failed to send cart reminder: {str(e)}")
        return None



def send_address_request(to):
    """Send address request message"""
    logger.info(f"Sending address request to {to}")
    
    message = "📍 *DELIVERY ADDRESS*\n\n" \
             "Please enter your full delivery address:\n\n" \
             "Example:\n" \
             "House No. 123, Street Name\n" \
             "Area, Landmark\n" \
             "City, PIN Code"
    
    return send_text_message(to, message)


def send_final_order_confirmation(to, order_id, address):
    """Send final order confirmation with address details"""
    logger.info(f"Sending final order confirmation to {to} for order {order_id}")
    
    # Get order
    order = redis_state.get_order(order_id)
    if not order:
        logger.error(f"Order {order_id} not found for final confirmation")
        return
    
    message = f"✅ *ORDER CONFIRMED*\n\n" \
             f"Order ID: #{order_id}\n" \
             f"Branch: {order['branch']}\n" \
             f"Payment Method: {order['payment_method']}\n\n"
    
    if order["delivery_type"] == "Delivery":
        message += "DELIVERY ADDRESS:\n"
        
        # Check if we have coordinates
        if isinstance(order["delivery_address"], dict) and "latitude" in order["delivery_address"]:
            latitude = order["delivery_address"]["latitude"]
            longitude = order["delivery_address"]["longitude"]
            maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            
            message += f"📍 {latitude}, {longitude}\n"
            message += f"🗺️ Map: {maps_link}\n\n"
            message += "Note: Delivery person will use this location for navigation\n\n"
        else:
            message += f"{address}\n\n"
    
    message += "ORDER ITEMS:\n"
    for item in order["items"]:
        item_total = item["quantity"] * item["price"]
        message += f"• {item['name']} x{item['quantity']} = ₹{item_total}\n"
    
    message += f"\n*TOTAL*: ₹{order['total']}\n\n" \
             "Your order will be processed shortly. Thank you for shopping with Kanuka Organics!"
    
    return send_text_message(to, message)



def send_order_alert(branch, order_id, items, total, sender, delivery_address, delivery_type):
    """Send order alert to branch with delivery address information"""
    logger.info(f"Sending order alert to {branch} for order {order_id}")
    
    from config.settings import BRANCH_CONTACTS
    
    if branch not in BRANCH_CONTACTS:
        logger.error(f"Branch {branch} not found in branch contacts")
        return
    
    to = BRANCH_CONTACTS[branch]
    
    message = "🔔 *NEW ORDER ALERT*\n\n" \
             f"Order ID: #{order_id}\n" \
             f"Customer: {sender}\n" \
             f"Delivery Type: {delivery_type}\n\n"
    
    
    delivery_address = redis_state.get_complete_delivery_info(sender)
    
    # Add delivery address information
    if delivery_type == "Delivery":
        message += "DELIVERY ADDRESS:\n"
        message += f"{delivery_address["text_address"]}\n\n"
        message += f"{delivery_address["maps_link"]}\n\n"
    
    message += "ORDER ITEMS:\n"
    for item in items:
        item_total = item["quantity"] * item["price"]
        message += f"• {item['name']} x{item['quantity']} = ₹{item_total}\n"
    
    message += f"\n*TOTAL*: ₹{total}\n\n" \
             "Please prepare this order as soon as possible."
    
    return send_text_message(to, message)