# services/order_service.py
import re
import uuid
import json
from datetime import datetime
from utils.logger import get_logger
from utils.csv_utils import log_order
from config.settings import BRANCH_CONTACTS, ORDER_STATUS, BRANCH_COORDINATES, DELIVERY_RADIUS_KM, PRODUCT_CATALOG
from stateHandlers.redis_state import redis_state
from services.whatsapp_service import (
    send_order_confirmation,
    send_order_status_update,
    send_payment_processing,
    send_payment_link,
    send_order_alert,
    send_text_message
)
import math

from utils.time_utils import get_current_ist

logger = get_logger("order_service")

def generate_order_id():
    """Generate a unique order ID"""
    return f"ORD{get_current_ist().strftime('%Y%m%d')}{str(uuid.uuid4())[:4].upper()}"

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

def find_nearest_branch(latitude, longitude):
    """Find the nearest branch based on coordinates"""
    nearest_branch = None
    min_distance = float('inf')
    
    for branch, coords in BRANCH_COORDINATES.items():
        distance = calculate_distance(
            latitude, longitude, coords[0], coords[1]
        )
        if distance < min_distance:
            min_distance = distance
            nearest_branch = branch
    
    return nearest_branch, min_distance

def is_within_delivery_radius(latitude, longitude):
    """Check if location is within delivery radius of any branch"""
    nearest_branch, distance = find_nearest_branch(latitude, longitude)
    return distance <= DELIVERY_RADIUS_KM, nearest_branch, distance

def process_payment(user_id, order_id):
    """Process payment for an order"""
    logger.info(f"Processing payment for user {user_id}, order {order_id}")
    
    # Send "payment link is generating" message
    send_payment_processing(user_id)
    
    # In a real implementation, this would call Razorpay API
    # For this example, we'll simulate a delay
    import time
    time.sleep(1)  # Simulate API delay
    
     # Get cart
    cart = redis_state.get_cart(user_id)
    
     # Get global discount
    discount_percentage = redis_state.get_global_discount()
    
      # Calculate original total
    original_total = cart["total"]
    
    # Apply discount
    discount_amount = 0
    discounted_total = original_total
    
    if discount_percentage > 0:
        discount_amount = (original_total * discount_percentage) / 100
        discounted_total = original_total - discount_amount
    
    # Send payment link
    send_payment_link(user_id, order_id,discounted_total)
    
    return True, "Payment link generated successfully"

# def update_order_status_from_command(command):
#     """Process order status update commands"""
#     logger.info(f"Processing order status command: {command}")
    
#     # Normalize command
#     command = command.lower().strip()
    
#     # Determine status and order ID
#     status = None
#     order_id = None
    
#     if "ready" in command:
#         status = ORDER_STATUS["READY"]
#     elif "ontheway" in command or "on the way" in command:
#         status = ORDER_STATUS["ON_THE_WAY"]
#     elif "delivered" in command:
#         status = ORDER_STATUS["DELIVERED"]
    
#     # Find order ID in command
#     import re
#     order_id_match = re.search(r'ord-[a-z0-9]+', command, re.IGNORECASE)
#     if order_id_match:
#         order_id = order_id_match.group(0).upper()
    
#     if not status or not order_id:
#         logger.warning(f"Invalid status update command: {command}")
#         return False, "Invalid command format. Use: [status] ORD-XXXX"
    
#     # Get order
#     order = redis_state.get_order(order_id)
#     if not order:
#         logger.warning(f"Order {order_id} not found for status update")
#         return False, f"Order {order_id} not found."
    
#     # Update order status
#     if redis_state.update_order_status(order_id, status):
#         # Send status update to customer
#         send_order_status_update(order["user_id"], order_id, status)
        
#         # If delivered, archive the order
#         if status == ORDER_STATUS["DELIVERED"]:
#             redis_state.archive_order(order_id)
#             logger.info(f"Order {order_id} archived after delivery")
        
#         return True, f"Order {order_id} status updated to {status}."
#     else:
#         return False, f"Failed to update status for order {order_id}."

def update_order_status_from_command(command):
    """Process order status update commands from staff"""
    logger.info(f"Processing order status command: {command}")
    
    # Normalize command
    command = command.lower().strip()
    
    # Determine status
    status = None
    if "ready" in command:
        status = ORDER_STATUS["READY"]
    elif "ontheway" in command or "on the way" in command:
        status = ORDER_STATUS["ON_THE_WAY"]
    elif "delivered" in command:
        status = ORDER_STATUS["DELIVERED"]
    
    # Find order ID in command (matches formats like FCT20250808E8BF or ORD20250808E8BF)
    order_id_match = re.search(r'[a-z]{3}\d{8}[a-z0-9]{4}', command, re.IGNORECASE)
    if order_id_match:
        order_id = order_id_match.group(0).upper()
    
    if not status or not order_id:
        logger.warning(f"Invalid status update command: {command}")
        return False, "Invalid command format. Use: [status] [order_id]\n\nExample: 'ready FCT20250808E8BF'"
    
    logger.info(f"Attempting to update order {order_id} to status: {status}")
    
    # Get order
    order = redis_state.get_order(order_id)
    if not order:
        logger.warning(f"Order {order_id} not found for status update")
        return False, f"Order {order_id} not found. Please check the order ID."
    
    # Update order status
    if redis_state.update_order_status(order_id, status):
        # Send status update to customer
        send_order_status_update(order["user_id"], order_id, status)
        
        # Special handling for delivered status
        if status == ORDER_STATUS["DELIVERED"]:
            redis_state.archive_order(order_id)
            logger.info(f"Order {order_id} archived after delivery")
            
        return True, f"✅ Order #{order_id} status updated to *{status}*."
    else:
        return False, f"❌ Failed to update status for order #{order_id}. Please try again."

def send_final_order_confirmation(to, order_id, address,branch_number,discount_percentage,discount_amount):
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
    
    if order["delivery_type"] == "Delivery" and address:
        message += "DELIVERY ADDRESS:\n" \
                  f"{address}\n\n"
    
    message += "ORDER ITEMS:\n"
    for item in order["items"]:
        item_total = item["quantity"] * item["price"]
        if discount_percentage > 0:
            message += f"• {item['name']} x{item['quantity']} | {discount_percentage}% Discount Applied: -₹{discount_amount} = ₹{item_total}\n"
        else:
            message += f"• {item['name']} x{item['quantity']} = ₹{item_total}\n"
    
    message += f"\n*TOTAL*: ₹{order['total']}\n\n" \
             "Your order will be processed shortly. Thank you for shopping!\n"
    message += f"📞for any queries contact our branch {branch_number} "
    
    return send_text_message(to, message)

def place_order(user_id, delivery_type, address=None, payment_method="Cash on Delivery"):
    """Place an order from user's cart - handles everything for COD orders"""
    logger.info(f"Placing order for user {user_id} with delivery type {delivery_type} and payment method {payment_method}")
    
    # Get cart
    cart = redis_state.get_cart(user_id)
    if not cart["items"]:
        logger.warning(f"Cart is empty for user {user_id}")
        return False, "Your cart is empty. Please add items before placing an order."
    
     # Get global discount
    discount_percentage = redis_state.get_global_discount()
    logger.info(f"Applying global discount of {discount_percentage}% to order for {user_id}")
    
    # Generate order ID
    order_id = generate_order_id()
    
    # Get branch information
    if delivery_type == "Delivery":
        # For delivery, we need location and nearest branch
        if "location" not in cart:
            logger.warning(f"Location not set for delivery order by {user_id}")
            return False, "Location not set. Please share your location first."
        
        location = cart["location"]
        within_radius, nearest_branch, distance = is_within_delivery_radius(
            location["latitude"], location["longitude"]
        )
        
        if not within_radius:
            logger.warning(f"User {user_id} is outside delivery radius (distance: {distance}km)")
            return False, f"Sorry, we don't deliver to your location. Nearest branch is {distance:.2f}km away."
        
        branch = nearest_branch
        delivery_address = location  # Use the location dict directly
    else:
        # For takeaway, branch is required
        if "branch" not in cart:
            logger.warning(f"Branch not set for takeaway order by {user_id}")
            return False, "Branch not selected. Please select a branch first."
        
        branch = cart["branch"]
        delivery_address = "Takeaway"  # Clear indicator for pickup
    
     # Calculate original total
    original_total = cart["total"]
    
    # Apply discount
    discount_amount = 0
    discounted_total = original_total
    
    if discount_percentage > 0:
        discount_amount = (original_total * discount_percentage) / 100
        discounted_total = original_total - discount_amount
    
    # Prepare order data
    order_data = {
        "order_id": order_id,
        "user_id": user_id,
        "branch": branch,
        "items": cart["items"],
        "original_total": original_total,
        "discount_percentage": discount_percentage,
        "discount_amount": discount_amount,
        "total": discounted_total,
        "status": ORDER_STATUS["PAID"] if payment_method == "Cash on Delivery" else ORDER_STATUS["PENDING"],
        "order_date": get_current_ist().strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_type": delivery_type,
        "delivery_address": delivery_address,
        "text_address": address,
        "payment_method": payment_method
    }
    
    # Save to Redis
    if not redis_state.create_order(order_data):
        logger.error(f"Failed to save order {order_id} to Redis")
        return False, "Failed to save order. Please try again."
    
    # Log order to CSV
    log_order(order_data)
    
    # Schedule cart reminder (won't apply since cart is cleared, but good for reference)
    redis_state.schedule_cart_reminder(user_id, order_id)
    
    # Send order alert to branch
    send_order_alert(
        branch,
        order_id,
        cart["items"],
        discounted_total,
        user_id,
        payment_method,
        discount_percentage,
        discount_amount,
        delivery_type
    )
    
    # Send order confirmation to customer
    send_final_order_confirmation(user_id, order_id, address,BRANCH_CONTACTS[branch][0],discount_percentage,discount_amount)
    
    return True, f"Order #{order_id} placed successfully!"

def confirm_order(whatsapp_number, order_id, payment_method):
    """Confirm order after payment - only for online payments"""
    logger.info(f"Confirming order {order_id} for {whatsapp_number}")
    
    # Get pending order
    pending_order_data = redis_state.redis.get(f"pending_order:{order_id}")
    if not pending_order_data:
        logger.error(f"Pending order {order_id} not found")
        return False
    
    # Decode if pending_order_data is bytes
    if isinstance(pending_order_data, bytes):
        pending_order_data = pending_order_data.decode('utf-8')
    
    try:
        pending_order = json.loads(pending_order_data)
        
        # Extract details
        user_id = pending_order["user_id"]
        cart = pending_order["cart"]
        delivery_type = pending_order["delivery_type"]
        address = pending_order["delivery_address"]
        
        # Place the actual order (this will send all notifications)
        success, message = place_order(user_id, delivery_type, address=address, payment_method="Pay Now")
        
        if success:
            # Delete pending order
            redis_state.redis.delete(f"pending_order:{order_id}")
            
            # CRITICAL FIX: Clear the cart and reset state
            redis_state.clear_cart(user_id)
            redis_state.clear_user_state(user_id)
            
            return True
        else:
            logger.error(f"Failed to place order from pending order: {message}")
            return False
    except Exception as e:
        logger.error(f"Error processing pending order: {str(e)}")
        return False