# # utils/csv_utils.py
# import csv
# import os
# from datetime import datetime
# from config.settings import Settings
# from utils.logger import get_logger

# logger = get_logger("csv_utils")

# def log_order(order_data: dict):
#     """Log order details to CSV file"""
#     today = datetime.utcnow().strftime("%Y-%m-%d")
#     filename = f"logs/orders_{today}.csv"
    
#     # Ensure logs directory exists
#     os.makedirs("logs", exist_ok=True)
    
#     # Write header if new file
#     write_header = not os.path.exists(filename)
    
#     try:
#         with open(filename, 'a', newline='') as f:
#             writer = csv.writer(f)
            
#             if write_header:
#                 writer.writerow([
#                     "timestamp", "order_id", "phone", "brand", 
#                     "items", "total", "delivery_type", "branch", "status"
#                 ])
            
#             # Format items
#             items = "|".join([
#                 f"{item['quantity']}x {item['name']}" 
#                 for item in order_data["items"]
#             ])
            
#             writer.writerow([
#                 order_data["created_at"],
#                 order_data["id"],
#                 order_data["phone"],
#                 order_data["brand"],
#                 items,
#                 f"{order_data['total']:.2f}",
#                 order_data["delivery_type"],
#                 order_data["branch"],
#                 order_data["status"]
#             ])
#         logger.info(f"Order logged: {order_data['id']}")
#     except Exception as e:
#         logger.error(f"CSV logging failed: {str(e)}")








# # utils/csv_utils.py
# import csv
# import os
# from datetime import datetime
# from config.credentials import CART_REMINDERS_CSV, ORDERS_CSV, USER_ACTIVITY_LOG_CSV
# from utils.logger import get_logger

# logger = get_logger("csv_utils")

# def append_to_csv(file_path, data):
#     """Append data to CSV file"""
#     try:
#         # Create directory if it doesn't exist
#         os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
#         # Check if file exists to determine if we need headers
#         file_exists = os.path.isfile(file_path)
        
#         with open(file_path, 'a', newline='') as csvfile:
#             # Get fieldnames from data keys
#             fieldnames = list(data.keys())
            
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
#             # Write header if file is new
#             if not file_exists:
#                 writer.writeheader()
            
#             # Write data
#             writer.writerow(data)
        
#         logger.info(f"Data appended to {file_path}")
#         return True
#     except Exception as e:
#         logger.error(f"Error appending to CSV {file_path}: {str(e)}")
#         return False

# def read_csv(file_path):
#     """Read data from CSV file"""
#     try:
#         if not os.path.isfile(file_path):
#             return []
        
#         with open(file_path, 'r') as csvfile:
#             reader = csv.DictReader(csvfile)
#             return list(reader)
#     except Exception as e:
#         logger.error(f"Error reading CSV {file_path}: {str(e)}")
#         return []

# def log_user_activity(user_id, action, details=""):
#     """Log user activity to CSV"""
#     try:
#         data = {
#             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "user_id": user_id,
#             "action": action,
#             "details": details
#         }
#         return append_to_csv(USER_ACTIVITY_LOG_CSV, data)
#     except Exception as e:
#         logger.error(f"Error logging user activity: {str(e)}")
#         return False

# def log_order(order_data):
#     """Log order details to CSV"""
#     try:
#         # Format order data for logging
#         log_data = {
#             "order_id": order_data["order_id"],
#             "user_id": order_data["user_id"],
#             "brand": order_data["brand"],
#             "branch": order_data["branch"],
#             "items": str(order_data["items"]),
#             "total": order_data["total"],
#             "status": order_data["status"],
#             "order_date": order_data["order_date"],
#             "payment_method": order_data.get("payment_method", "N/A"),
#             "delivery_address": order_data.get("delivery_address", "N/A"),
#             "latitude": order_data.get("latitude", "N/A"),
#             "longitude": order_data.get("longitude", "N/A")
#         }
#         return append_to_csv(ORDERS_CSV, log_data)
#     except Exception as e:
#         logger.error(f"Error logging order: {str(e)}")
#         return False

# def log_cart_reminder(user_id, order_id):
#     """Log cart reminder to CSV"""
#     try:
#         data = {
#             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "user_id": user_id,
#             "order_id": order_id
#         }
#         return append_to_csv(CART_REMINDERS_CSV, data)
#     except Exception as e:
#         logger.error(f"Error logging cart reminder: {str(e)}")
#         return False




# utils/csv_utils.py
import csv
import os
from datetime import datetime
from config.credentials import CART_REMINDERS_CSV, ORDERS_CSV, USER_ACTIVITY_LOG_CSV
from utils.logger import get_logger
from config.settings import BRAND_NAME
from utils.time_utils import get_current_ist

logger = get_logger("csv_utils")

def append_to_csv(file_path, data):
    """Append data to CSV file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.isfile(file_path)
        
        with open(file_path, 'a', newline='') as csvfile:
            # Get fieldnames from data keys
            fieldnames = list(data.keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write data
            writer.writerow(data)
        
        logger.info(f"Data appended to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error appending to CSV {file_path}: {str(e)}")
        return False

def log_user_activity(user_id, action, details=""):
    """Log user activity to CSV"""
    try:
        data = {
            "timestamp": get_current_ist().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "action": action,
            "details": details
        }
        
        # Log to user activity log
        append_to_csv(USER_ACTIVITY_LOG_CSV, data)
        
        return True
    except Exception as e:
        logger.error(f"Error logging user activity: {str(e)}")
        return False

def log_order(order_data):
    """Log order details to CSV"""
    try:
        # Format order data for logging
        log_data = {
            "order_id": order_data["order_id"],
            "user_id": order_data["user_id"],
            "brand": BRAND_NAME,
            "branch": order_data["branch"],
            "items": str(order_data["items"]),
            "total": order_data["total"],
            "status": order_data["status"],
            "order_date": order_data["order_date"],
            "delivery_type": order_data["delivery_type"],
            "payment_method": order_data["payment_method"]
        }
        return append_to_csv(ORDERS_CSV, log_data)
    except Exception as e:
        logger.error(f"Error logging order: {str(e)}")
        return False

def log_cart_reminder(user_id, order_id):
    """Log cart reminder to CSV"""
    try:
        data = {
            "timestamp": get_current_ist().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "order_id": order_id
        }
        return append_to_csv(CART_REMINDERS_CSV, data)
    except Exception as e:
        logger.error(f"Error logging cart reminder: {str(e)}")
        return False