

# META_ACCESS_TOKEN = "EAASgG9eRTmYBPJ7Takvau9H1RLk3UTEkrevSPfqhWKXmkqLhaip6GeBYKrDhrol5Q91JRi4DaeZCmkgIMTIKKkA2VBt4csl7l05JAt8aUOSvwjvFS26gPUYbDBja6RpBpxybgX0byLXFsW8lkgDYkh0ieJFKCFFheVH0IZCFwq8fwc8AQPxLrZAqlip0igo"
# META_PHONE_NUMBER_ID = "747499348442635"
# META_VERIFY_TOKEN = "kanuka123"
# GOOGLE_MAPS_API_KEY = "AIzaSyCuUz9N78WZAT1N38ffIDkbySI3_0zkZgE"
# RAZORPAY_KEY_ID = "rzp_live_jtGMQ5k5QGHxFg"
# RAZORPAY_KEY_SECRET = "FEMHAO4zeUFnAiKZPLe44NRN"
# WHATSAPP_API_URL = f"https://graph.facebook.com/v23.0/{META_PHONE_NUMBER_ID}/messages" 
# CATALOG_ID = "1454851805648535"
# CATALOG_ID_FOR_MATCHED_ITEMS = "1454851805648535"


# config/credentials.py
# import os

# class Credentials:
#     REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
#     RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
#     RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")
#     WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")
#     WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
#     PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
#     VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
#     ADMIN_PHONE = os.getenv("ADMIN_PHONE")  # For order alerts
#     CATALOG_ID = os.getenv("CATALOG_ID")  # For order alerts
#     CATALOG_ID_FOR_MATCHED_ITEMS = os.getenv("CATALOG_ID_FOR_MATCHED_ITEMS")  # For order alerts


# config/credentials.py

# WhatsApp API credentials
META_ACCESS_TOKEN = "EAASgG9eRTmYBPOUpKGuAYED0616Pn3F1gfTwQ0Hxp5vYsKxFgAnfDXXU0XnWePwqiIuIM2S3t5XYJrZB59AS9t9IVoZBUp9qHY1Pk3aMTbh9cHXyDLntUJKZC3TmwABjoS2JB2iUzXq0TKMRMdWnov9OqSPx2JhZCQJMQZCckxZASvWWByLgmriYzgKGBUS1aW"
META_PHONE_NUMBER_ID = "747499348442635"
WHATSAPP_API_URL = f"https://graph.facebook.com/v23.0/{META_PHONE_NUMBER_ID}/messages"
WHATSAPP_CATALOG_ID = "1454851805648535"  # Optional, if using WhatsApp Catalog

# Verification token for webhook
META_VERIFY_TOKEN = "kanuka123"

# Redis connection
REDIS_URL = "redis://localhost:6379/0"

# Razorpay credentials
RAZORPAY_KEY_ID = "rzp_live_jtGMQ5k5QGHxFg"
RAZORPAY_KEY_SECRET = "FEMHAO4zeUFnAiKZPLe44NRN"

GOOGLE_MAPS_API_KEY = "AIzaSyCuUz9N78WZAT1N38ffIDkbySI3_0zkZgE"

# CSV file paths (relative to project root)
ORDERS_CSV = "../data/orders.csv"
CART_REMINDERS_CSV = "../data/cart_reminders.csv"
USER_ACTIVITY_LOG_CSV = "../data/user_activity_log.csv"
BRANCHES_CSV = "../data/branches.csv"
BRANDS_CSV = "../data/brands.csv"
