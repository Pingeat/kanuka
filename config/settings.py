# # config/settings.py
# from datetime import timedelta

# class Settings:
#     # Brand configuration
#     BRAND_CONFIG_PATH = "config/brands/"
    
#     # Order processing
#     DELIVERY_RADIUS_KM = 4.0
#     CART_REMINDER_DELAY = timedelta(hours=1)
#     DAILY_REMINDER_INTERVAL = timedelta(days=1)
#     ORDER_RETENTION_PERIOD = timedelta(days=2)
    
#     # Branch coordinates (example - should be in brand config)
#     BRANCH_COORDINATES = {
#         "kondapur": (17.4449, 78.3491),
#         "madhapur": (17.4509, 78.3809),
#         "manikonda": (17.4291, 78.3593),
#         "nizampet": (17.5050, 78.3500),
#         "nanakramguda": (17.4457, 78.3914)
#     }
    
#     # Redis keys
#     USER_STATE_KEY = "user:state:{phone}"
#     PENDING_CARTS_KEY = "carts:pending"
#     ORDERS_KEY = "orders:{order_id}"
#     BRAND_CONFIG_KEY = "brand:config:{brand_id}"



# config/settings.py

# Brand configuration
BRAND_NAME = "Kanuka Organics"
GREETING_MESSAGE = "🌿 *Welcome to Kanuka Organics*\n\n" \
                  "Your one-stop shop for premium organic products!\n\n" \
                  "How can we help you today?"

# Branch contacts (for order notifications)
BRANCH_CONTACTS = {
    "Kondapur": ["916302588275"],
    "Madhapur": ["917075442898"],
    "Manikonda": ["919392016847"],
    "Nizampet": ["916303241076"],
    "Nanakramguda": ["916303237242"],
    "Madhapur": ["919640112005"]
}

OTHER_NUMBERS = ["9640112005", "9226454238","8074301029"]

# Branch coordinates (latitude, longitude)
BRANCH_COORDINATES = {
    "Kondapur": (17.4354, 78.3775),
    "Madhapur": (17.4409, 78.3490),
    "Manikonda": (17.4578, 78.3701),
    "Nizampet": (17.5152, 78.3385),
    "Nanakramguda": (17.4632, 78.3813),
    "Madhapur": (17.453257381591207, 78.39550445225969),
    "West Maredpally": (17.4558529177458, 78.50727064061495)
}

# Delivery radius in kilometers
DELIVERY_RADIUS_KM = 6.0

# Cart reminder settings
CART_REMINDER_INTERVAL_HOURS = 2
DAILY_REMINDER_TIME = "10:00"  # 10 AM

# Order status
ORDER_STATUS = {
    "PENDING": "Pending",
    "PAID": "Paid",
    "READY": "Ready",
    "ON_THE_WAY": "On The Way",
    "DELIVERED": "Delivered",
    "CANCELLED": "Cancelled"
}

# Order status progression
ORDER_STATUS = {
    "PENDING": "Pending",
    "PAID": "Paid",
    "READY": "Ready",
    "ON_THE_WAY": "On The Way",
    "DELIVERED": "Delivered",
    "CANCELLED": "Cancelled"
}

# Payment methods
PAYMENT_METHODS = ["Pay Now", "Cash on Delivery"]

# WhatsApp Catalog product ID to name mapping
PRODUCT_CATALOG = {
    "6xpxtkaoau": {"name": "Palm Jaggery - Powdered(700gms)", "price": 760},
    "kyygkhdlxf": {"name": "Palm Jaggery - cubes(1 KG)","price": 1100},
    "1ado92c3xm": {"name": "Palm Jaggery - Powdered(1 KG)", "price": 1100},
    "36dlxrjdjq": {"name": "Palm Jaggery - Powdered(500gms)", "price": 550},
    "hkaqqb8sec": {"name": "Palm Jaggery - cubes(500gms)", "price": 550},
}

# Bulk order contact information
BULK_ORDER_CONTACT = {
    "phone": "919876543210",
    "email": "bulk@kanukaorganics.com"
}


ADMIN_NUMBERS = ["918074301029","919640112005"]

# Current active brand (can be changed dynamically)
# ACTIVE_BRAND = "default"

# def get_brand_config(brand_name=None):
#     """Get configuration for a specific brand or the active brand"""
#     if brand_name is None:
#         brand_name = ACTIVE_BRAND
    
#     if brand_name in BRAND_CONFIG:
#         return BRAND_CONFIG[brand_name]
    
#     # Return default if brand not found
#     return BRAND_CONFIG["default"]

# def set_active_brand(brand_name):
#     """Set the active brand"""
#     global ACTIVE_BRAND
#     if brand_name in BRAND_CONFIG:
#         ACTIVE_BRAND = brand_name
#         return True
#     return False