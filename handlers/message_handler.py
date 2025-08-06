# handlers/message_handler.py
from datetime import datetime
import json
import traceback
import uuid
from config.settings import BRANCH_COORDINATES, DELIVERY_RADIUS_KM, GREETING_MESSAGE, ORDER_STATUS, PRODUCT_CATALOG
from stateHandlers.redis_state import redis_state
from services.whatsapp_service import (
    send_address_request,
    send_main_menu,
    send_catalog,
    send_cart_summary,
    send_delivery_options,
    send_location_request,
    send_branch_selection,
    send_payment_options,
    send_bulk_order_info,
    send_payment_processing,
    send_text_message
)
from services.order_service import (
    place_order,
    process_payment,
    confirm_order,
    send_final_order_confirmation,
    update_order_status_from_command
)
from utils.logger import get_logger
from utils.csv_utils import log_user_activity
import re
import math

logger = get_logger("message_handler")

def handle_incoming_message(data):
    """Handle incoming WhatsApp messages"""
    logger.info("Received message data")
    
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                if not messages:
                    continue
                
                msg = messages[0]
                sender = msg.get("from").lstrip('+')  # Normalize sender ID
                message_type = msg.get("type")
                
                # Log activity
                if message_type == "text":
                    text = msg.get("text", {}).get("body", "").strip().lower()
                    logger.info(f"Message received from {sender}: {text}")
                    log_user_activity(sender, "message_received", f"Text: {text}")
                
                # Get current state
                current_state = redis_state.get_user_state(sender)
                logger.debug(f"Current state for {sender}: {current_state}")
                
                # INTERACTIVE MESSAGE HANDLING
                if message_type == "interactive":
                    interactive_type = msg.get("interactive", {}).get("type")
                    if interactive_type == "list_reply":
                        # Handle branch selection from list
                        selected_branch = msg.get("interactive", {}).get("list_reply", {}).get("id")
                        handle_branch_selection(sender, selected_branch, current_state)
                    elif interactive_type == "button_reply":
                        # Handle button responses
                        button_id = msg.get("interactive", {}).get("button_reply", {}).get("id")
                        handle_button_response(sender, button_id, current_state)
                    elif interactive_type == "catalog_message":
                        # Handle catalog selection
                        catalog_id = msg.get("interactive", {}).get("catalog_message", {}).get("catalog_id")
                        product_retailer_id = msg.get("interactive", {}).get("catalog_message", {}).get("product_retailer_id")
                        handle_catalog_selection(sender, product_retailer_id, current_state)
                
                # TEXT MESSAGE HANDLING
                elif message_type == "text":
                    text = msg.get("text", {}).get("body", "").strip().lower()
                    handle_text_message(sender, text, current_state)
                
                # ORDER MESSAGE HANDLING
                elif message_type == "order":
                    items = msg.get("order", {}).get("product_items", [])
                    handle_catalog_order(sender, items)
                
                # LOCATION MESSAGE HANDLING
                elif message_type == "location":
                    # Handle location sharing
                    latitude = msg.get("location", {}).get("latitude")
                    longitude = msg.get("location", {}).get("longitude")
                    handle_location(sender, latitude, longitude, current_state)
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Message handler error: {str(e)}\n{traceback.format_exc()}")
        return "Error processing message", 500

def handle_branch_selection(sender, selected_branch, current_state):
    """Handle branch selection from interactive list"""
    logger.info(f"Handling branch selection for {sender}: {selected_branch}")
    
    # Validate branch
    valid_branch = None
    for b in BRANCH_COORDINATES.keys():
        if b.lower() == selected_branch.lower():
            valid_branch = b
            break
    
    if not valid_branch:
        logger.error(f"Invalid branch selected by {sender}: {selected_branch}")
        send_text_message(sender, "❌ Invalid branch selection. Please try again.")
        send_branch_selection(sender)
        return
    
    # Set branch in cart
    redis_state.set_branch(sender, valid_branch)
    
    # Set delivery type to Takeaway
    redis_state.set_delivery_type(sender, "Takeaway")
    
    # Ask for payment method
    send_payment_options(sender)
    redis_state.set_user_state(sender, {"step": "SELECTING_PAYMENT_METHOD", "branch": valid_branch})

def handle_button_response(sender, button_id, current_state):
    """Handle button responses from user"""
    logger.info(f"Handling button response for {sender}: {button_id}")
    
    # Handle main menu options
    if button_id == "ORDER_NOW":
        send_catalog(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CATALOG"})
    
    elif button_id == "BULK_ORDERS":
        send_bulk_order_info(sender)
        redis_state.clear_user_state(sender)
    
    # Handle cart interaction
    elif button_id == "CONTINUE_SHOPPING":
        send_catalog(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CATALOG"})
    
    elif button_id == "PROCEED_TO_CHECKOUT":
        send_delivery_options(sender)
        redis_state.set_user_state(sender, {"step": "SELECTING_DELIVERY_TYPE"})
    
    elif button_id == "CLEAR_CART":
        redis_state.clear_cart(sender)
        send_text_message(sender, "🗑️ Your cart has been cleared.")
        send_catalog(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CATALOG"})
    
    # Handle delivery type selection
    elif current_state and current_state.get("step") == "SELECTING_DELIVERY_TYPE":
        if button_id == "DELIVERY":
            send_location_request(sender)
            redis_state.set_delivery_type(sender, "Delivery")
            redis_state.set_user_state(sender, {"step": "WAITING_FOR_LOCATION"})
        elif button_id == "TAKEAWAY":
            send_branch_selection(sender)
            redis_state.set_delivery_type(sender, "Takeaway")
            redis_state.set_user_state(sender, {"step": "SELECTING_BRANCH"})
    
    # Handle payment options
    elif current_state and current_state.get("step") == "SELECTING_PAYMENT_METHOD":
        if button_id == "PAY_NOW":
            redis_state.set_payment_method(sender, "Pay Now")
            # Ask for address first
            send_address_request(sender)
            redis_state.set_user_state(sender, {"step": "WAITING_FOR_ADDRESS", "payment_method": "Pay Now"})
        elif button_id == "CASH_ON_DELIVERY":
            redis_state.set_payment_method(sender, "Cash on Delivery")
            # Ask for address first
            send_address_request(sender)
            redis_state.set_user_state(sender, {"step": "WAITING_FOR_ADDRESS", "payment_method": "Cash on Delivery"})

def handle_location(sender, latitude, longitude, current_state):
    """Handle location sharing from user"""
    logger.info(f"Handling location for {sender}: {latitude}, {longitude}")
    
    # Set location in cart
    redis_state.set_location(sender, latitude, longitude)
    
    # Check if within delivery radius
    within_radius, nearest_branch, distance = is_within_delivery_radius(latitude, longitude)
    
    if within_radius:
        # Set branch in cart
        redis_state.set_branch(sender, nearest_branch)
        
        # Ask for payment method
        send_payment_options(sender)
        redis_state.set_user_state(sender, {"step": "SELECTING_PAYMENT_METHOD", "branch": nearest_branch})
    else:
        message = f"❌ Sorry, we don't deliver to your location.\n" \
                 f"The nearest branch is {distance:.2f}km away, but our delivery radius is only {DELIVERY_RADIUS_KM}km."
        send_text_message(sender, message)

def handle_text_message(sender, text, current_state):
    """Handle text messages from users"""
    logger.info(f"Handling text message from {sender}: {text}")
    
    # Handle order status update commands from staff
    status_update_match = re.search(r'(ready|ontheway|on the way|delivered)\s+ord-[a-z0-9]+', text, re.IGNORECASE)
    if status_update_match:
        success, message = update_order_status_from_command(text)
        send_text_message(sender, message)
        return
    
    # Handle address input
    if current_state and current_state.get("step") == "WAITING_FOR_ADDRESS":
        payment_method = current_state.get("payment_method", "Cash on Delivery")
        address = text.strip()
        
        # Store address
        redis_state.set_delivery_address(sender, address)
        
        # Get cart
        cart = redis_state.get_cart(sender)
        delivery_type = cart.get("delivery_type", "Takeaway")
        
        if payment_method == "Cash on Delivery":
            # For Cash on Delivery, immediately place the order
            order_id, message = place_order(sender, delivery_type)
            
            if order_id:
                # Confirm the order
                confirm_order(sender, order_id, payment_method, address=address)
                
                # Clear the cart
                redis_state.clear_cart(sender)
                
                # Send final confirmation
                send_final_order_confirmation(sender, order_id, address)
            else:
                send_text_message(sender, f"❌ Failed to place order: {message}")
            
            # Reset state
            redis_state.clear_user_state(sender)
        elif payment_method == "Pay Now":
            # For online payment, generate payment link and wait for confirmation
            send_payment_processing(sender)
            
            # Generate order ID but don't place order yet
            order_id = generate_order_id()
            
            # Store order details as pending
            pending_order = {
                "order_id": order_id,
                "user_id": sender,
                "cart": cart,
                "delivery_type": delivery_type,
                "delivery_address": address,
                "status": "PENDING_PAYMENT",
                "payment_method": "Pay Now"
            }
            redis_state.redis.setex(f"pending_order:{order_id}", 3600, json.dumps(pending_order))
            
            # Process payment (generates link)
            success, message = process_payment(sender, order_id)
            
            if not success:
                send_text_message(sender, f"❌ Failed to generate payment link: {message}")
                # Clear pending order
                redis_state.redis.delete(f"pending_order:{order_id}")
                # Reset state
                redis_state.clear_user_state(sender)
        else:
            send_text_message(sender, "❌ Invalid payment method. Please try again.")
            # Reset state
            redis_state.clear_user_state(sender)
        
        return
    
    # Reset to main menu if state is invalid or missing
    if not current_state or current_state.get("step") not in ["VIEWING_CATALOG", "VIEWING_CART", "SELECTING_DELIVERY_TYPE", "WAITING_FOR_LOCATION", "SELECTING_BRANCH", "SELECTING_PAYMENT_METHOD", "WAITING_FOR_ADDRESS"]:
        logger.info(f"Resetting state for {sender} - invalid or missing state: {current_state}")
        redis_state.clear_user_state(sender)
        send_main_menu(sender)
        redis_state.set_user_state(sender, {"step": "MAIN_MENU"})
        return
    
    # Handle common greetings in any state
    greetings = ["hi", "hello", "hey", "hii", "namaste"]
    if any(greeting in text for greeting in greetings):
        logger.info(f"User {sender} sent greeting '{text}', resetting to main menu")
        redis_state.clear_user_state(sender)
        send_main_menu(sender)
        redis_state.set_user_state(sender, {"step": "MAIN_MENU"})
        return
    
    # Handle cart command in any state
    if "cart" in text or "my cart" in text:
        send_cart_summary(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CART"})
        return
    
    # Handle main menu options
    if current_state.get("step") == "MAIN_MENU":
        # Already handled by buttons, but just in case
        send_main_menu(sender)
    
    # Handle catalog interaction
    elif current_state.get("step") == "VIEWING_CATALOG":
        # This is handled by catalog selection, not text
        send_catalog(sender)
    
    # Handle cart interaction
    elif current_state.get("step") == "VIEWING_CART":
        # This is handled by cart buttons
        send_cart_summary(sender)
    
    # Handle delivery type selection
    elif current_state.get("step") == "SELECTING_DELIVERY_TYPE":
        # This is handled by delivery buttons
        send_delivery_options(sender)


def handle_catalog_selection(sender, product_retailer_id, current_state):
    """Handle product selection from catalog"""
    logger.info(f"Handling catalog selection for {sender}: {product_retailer_id}")
    
    if not current_state or current_state.get("step") != "VIEWING_CATALOG":
        send_catalog(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CATALOG"})
        return
    
    # Get product info from catalog mapping
    product_info = PRODUCT_CATALOG.get(product_retailer_id)
    
    if product_info:
        # Add to cart (quantity 1 by default)
        cart = redis_state.add_to_cart(sender, product_retailer_id, 1)
        
        # Send cart summary
        send_cart_summary(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CART"})
        
        logger.info(f"Added 1x {product_info['name']} (ID: {product_retailer_id}) to cart for {sender}")
    else:
        logger.warning(f"Unknown product ID selected: {product_retailer_id} for sender {sender}")
        send_text_message(sender, "❌ Product not found. Please try again.")

def handle_catalog_order(sender, items):
    """Handle catalog orders (when user selects from WhatsApp catalog)"""
    logger.info(f"Handling catalog order from {sender}")
    
    # Get user's current state
    current_state = redis_state.get_user_state(sender)
    logger.debug(f"[CATALOG ITEMS]: {items}")
    
    # If not in catalog view, prompt for catalog
    if not current_state or current_state.get("step") != "VIEWING_CATALOG":
        send_catalog(sender)
        redis_state.set_user_state(sender, {"step": "VIEWING_CATALOG"})
        return
    
    # Add catalog items to cart
    for item in items:
        product_id = item.get("product_retailer_id", "")
        quantity = int(item.get("quantity", 1))
        
        # Get product info from catalog mapping
        product_info = PRODUCT_CATALOG.get(product_id)
        
        if product_info:
            # Add to cart
            redis_state.add_to_cart(sender, product_id, quantity)
            logger.info(f"Added {quantity}x {product_info['name']} (ID: {product_id}) to cart for {sender}")
        else:
            logger.warning(f"Unknown product ID: {product_id} for sender {sender}")
    
    # Send cart summary
    send_cart_summary(sender)
    redis_state.set_user_state(sender, {"step": "VIEWING_CART"})

def is_within_delivery_radius(latitude, longitude):
    """Check if location is within delivery radius of any branch"""
    nearest_branch = None
    min_distance = float('inf')
    
    for branch, coords in BRANCH_COORDINATES.items():
        distance = calculate_distance(
            latitude, longitude, coords[0], coords[1]
        )
        if distance < min_distance:
            min_distance = distance
            nearest_branch = branch
    
    return min_distance <= DELIVERY_RADIUS_KM, nearest_branch, min_distance

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def generate_order_id():
    """Generate a unique order ID"""
    return f"ORD{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:4].upper()}"