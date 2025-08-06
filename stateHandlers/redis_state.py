# # stateHandlers/redis_state.py
# import json
# import redis
# from config.settings import Settings
# from utils.logger import get_logger

# logger = get_logger("redis_state")

# class RedisState:
#     def __init__(self, redis_url):
#         self.redis = redis.from_url(redis_url)
#         self.settings = Settings()
    
#     def get_state(self, phone: str) -> dict:
#         """Get current user state"""
#         key = self.settings.USER_STATE_KEY.format(phone=phone)
#         state = self.redis.get(key)
#         return json.loads(state) if state else self._default_state()
    
#     def update_state(self, phone: str, updates: dict):
#         """Update user state with new values"""
#         state = self.get_state(phone)
#         state.update(updates)
#         key = self.settings.USER_STATE_KEY.format(phone=phone)
#         self.redis.setex(
#             key, 
#             int(self.settings.ORDER_RETENTION_PERIOD.total_seconds() * 2), 
#             json.dumps(state)
#         )
    
#     def clear_state(self, phone: str):
#         """Clear user state after order completion"""
#         key = self.settings.USER_STATE_KEY.format(phone=phone)
#         self.redis.delete(key)
    
#     def add_pending_cart(self, phone: str, cart_expiry: int):
#         """Add user to pending cart reminder queue"""
#         self.redis.zadd(
#             self.settings.PENDING_CARTS_KEY,
#             {phone: cart_expiry}
#         )
    
#     def remove_pending_cart(self, phone: str):
#         """Remove user from pending cart reminders"""
#         self.redis.zrem(self.settings.PENDING_CARTS_KEY, phone)
    
#     def _default_state(self) -> dict:
#         """Initialize default state structure"""
#         return {
#             "brand": None,
#             "step": "start",
#             "cart": {"items": [], "added_at": None},
#             "delivery": {
#                 "type": None,
#                 "location": None,
#                 "branch": None,
#                 "order_id": None
#             }
#         }











# # stateHandlers/redis_state.py
# import redis
# import json
# from config.credentials import REDIS_URL
# from utils.logger import get_logger
# from datetime import datetime, timedelta

# logger = get_logger("redis_state")

# class RedisState:
#     def __init__(self):
#         try:
#             self.redis = redis.from_url(REDIS_URL)
#             self.redis.ping()
#             logger.info("Connected to Redis successfully")
#         except Exception as e:
#             logger.error(f"Failed to connect to Redis: {str(e)}")
#             raise

#     def get_user_state(self, user_id):
#         """Get user state from Redis"""
#         try:
#             state = self.redis.get(f"user:{user_id}:state")
#             if state:
#                 # Decode if state is bytes
#                 if isinstance(state, bytes):
#                     state = state.decode('utf-8')
#                 return json.loads(state)
#             return None
#         except Exception as e:
#             logger.error(f"Error getting user state for {user_id}: {str(e)}")
#             return None

#     def set_user_state(self, user_id, state):
#         """Set user state in Redis"""
#         try:
#             # Add timestamp for debugging
#             state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             self.redis.setex(f"user:{user_id}:state", 3600, json.dumps(state))  # 1 hour expiry
#             logger.debug(f"Set user state for {user_id}: {state}")
#             return True
#         except Exception as e:
#             logger.error(f"Error setting user state for {user_id}: {str(e)}")
#             return False

#     def clear_user_state(self, user_id):
#         """Clear user state from Redis"""
#         try:
#             self.redis.delete(f"user:{user_id}:state")
#             logger.debug(f"Cleared user state for {user_id}")
#             return True
#         except Exception as e:
#             logger.error(f"Error clearing user state for {user_id}: {str(e)}")
#             return False

#     def get_cart(self, user_id):
#         """Get user's cart from Redis"""
#         try:
#             cart = self.redis.get(f"user:{user_id}:cart")
#             if cart:
#                 # Decode if cart is bytes
#                 if isinstance(cart, bytes):
#                     cart = cart.decode('utf-8')
#                 cart_data = json.loads(cart)
#                 # Validate cart structure
#                 if "items" not in cart_data:
#                     cart_data["items"] = []
#                 if "brand" not in cart_data:
#                     cart_data["brand"] = "default"
#                 if "total" not in cart_data:
#                     cart_data["total"] = 0
#                 return cart_data
#             return {"items": [], "brand": "default", "total": 0}
#         except Exception as e:
#             logger.error(f"Error getting cart for {user_id}: {str(e)}")
#             return {"items": [], "brand": "default", "total": 0}

#     def add_to_cart(self, user_id, item, quantity, price=0, brand="default"):
#         """Add item to user's cart"""
#         try:
#             cart = self.get_cart(user_id)
            
#             # Set brand if not set
#             if not cart["brand"] or cart["brand"] == "default":
#                 cart["brand"] = brand
            
#             # Check if item already in cart
#             item_found = False
#             for cart_item in cart["items"]:
#                 if cart_item["name"].lower() == item.lower():
#                     cart_item["quantity"] += quantity
#                     item_found = True
#                     break
            
#             if not item_found:
#                 cart["items"].append({
#                     "name": item,
#                     "quantity": quantity,
#                     "price": price
#                 })
            
#             # Update total
#             cart["total"] = sum(item["quantity"] * item["price"] for item in cart["items"])
            
#             # Set expiry to 24 hours
#             self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
#             logger.debug(f"Added {quantity}x {item} to cart for {user_id}. Brand: {cart['brand']}")
#             return cart
#         except Exception as e:
#             logger.error(f"Error adding to cart for {user_id}: {str(e)}")
#             return self.get_cart(user_id)

#     def clear_cart(self, user_id):
#         """Clear user's cart"""
#         try:
#             self.redis.delete(f"user:{user_id}:cart")
#             logger.debug(f"Cleared cart for {user_id}")
#             return True
#         except Exception as e:
#             logger.error(f"Error clearing cart for {user_id}: {str(e)}")
#             return False

#     def set_branch(self, user_id, branch):
#         """Set user's selected branch"""
#         try:
#             cart = self.get_cart(user_id)
#             cart["branch"] = branch
#             self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
#             # Log branch selection
#             logger.info(f"Branch set for {user_id}: {branch}")
#             return True
#         except Exception as e:
#             logger.error(f"Error setting branch for {user_id}: {str(e)}")
#             return False

#     def set_location(self, user_id, latitude, longitude):
#         """Set user's location"""
#         try:
#             cart = self.get_cart(user_id)
#             cart["location"] = {
#                 "latitude": latitude,
#                 "longitude": longitude
#             }
#             self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
#             # Log location
#             logger.info(f"Location set for {user_id}: {latitude}, {longitude}")
#             return True
#         except Exception as e:
#             logger.error(f"Error setting location for {user_id}: {str(e)}")
#             return False

#     def set_payment_method(self, user_id, payment_method):
#         """Set user's payment method"""
#         try:
#             cart = self.get_cart(user_id)
#             cart["payment_method"] = payment_method
#             self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
#             # Log payment method
#             logger.info(f"Payment method set for {user_id}: {payment_method}")
#             return True
#         except Exception as e:
#             logger.error(f"Error setting payment method for {user_id}: {str(e)}")
#             return False

#     def create_order(self, order_data):
#         """Create a new order in Redis"""
#         try:
#             order_id = order_data["order_id"]
            
#             # Add to main orders list
#             self.redis.rpush("orders:all", json.dumps(order_data))
            
#             # Add to brand-specific list
#             self.redis.rpush(f"orders:brand:{order_data['brand']}", json.dumps(order_data))
            
#             # Add to branch-specific list
#             self.redis.rpush(f"orders:branch:{order_data['branch'].lower()}", json.dumps(order_data))
            
#             # Set as active for 7 days
#             self.redis.setex(f"order:{order_id}:active", 604800, "1")  # 7 days
            
#             logger.info(f"Order {order_id} created in Redis")
#             return True
#         except Exception as e:
#             logger.error(f"Error creating order in Redis: {str(e)}")
#             return False

#     def get_order(self, order_id):
#         """Get order details from Redis"""
#         try:
#             # Check if order is active
#             if not self.redis.exists(f"order:{order_id}:active"):
#                 return None
            
#             # Search in all orders
#             all_orders = self.redis.lrange("orders:all", 0, -1)
#             for order_str in all_orders:
#                 # Decode if order_str is bytes
#                 if isinstance(order_str, bytes):
#                     order_str = order_str.decode('utf-8')
                
#                 order = json.loads(order_str)
#                 if order["order_id"] == order_id:
#                     return order
            
#             return None
#         except Exception as e:
#             logger.error(f"Error getting order {order_id}: {str(e)}")
#             return None

#     def update_order_status(self, order_id, status):
#         """Update order status in Redis"""
#         try:
#             order = self.get_order(order_id)
#             if not order:
#                 return False
            
#             # Update status
#             order["status"] = status
#             order["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
#             # Remove old order
#             order_json = json.dumps(order, sort_keys=True)
#             self.redis.lrem("orders:all", 0, order_json)
            
#             # Add updated order
#             self.redis.rpush("orders:all", json.dumps(order))
            
#             # Update in brand-specific list
#             brand_list_key = f"orders:brand:{order['brand']}"
#             self.redis.lrem(brand_list_key, 0, order_json)
#             self.redis.rpush(brand_list_key, json.dumps(order))
            
#             # Update in branch-specific list
#             branch_list_key = f"orders:branch:{order['branch'].lower()}"
#             self.redis.lrem(branch_list_key, 0, order_json)
#             self.redis.rpush(branch_list_key, json.dumps(order))
            
#             logger.info(f"Order {order_id} status updated to {status}")
#             return True
#         except Exception as e:
#             logger.error(f"Error updating order {order_id} status: {str(e)}")
#             return False

#     def archive_order(self, order_id):
#         """Archive an order after delivery"""
#         try:
#             order = self.get_order(order_id)
#             if not order:
#                 return False
            
#             # Add to archive
#             self.redis.rpush("orders:archive", json.dumps(order))
            
#             # Remove from active lists
#             order_json = json.dumps(order, sort_keys=True)
#             self.redis.lrem("orders:all", 0, order_json)
#             self.redis.lrem(f"orders:brand:{order['brand']}", 0, order_json)
#             self.redis.lrem(f"orders:branch:{order['branch'].lower()}", 0, order_json)
            
#             # Delete active flag
#             self.redis.delete(f"order:{order_id}:active")
            
#             logger.info(f"Order {order_id} archived successfully")
#             return True
#         except Exception as e:
#             logger.error(f"Error archiving order {order_id}: {str(e)}")
#             return False

#     def schedule_cart_reminder(self, user_id, order_id, delay_hours=2):
#         """Schedule a cart reminder"""
#         try:
#             reminder_time = datetime.now() + timedelta(hours=delay_hours)
#             reminder_data = {
#                 "user_id": user_id,
#                 "order_id": order_id,
#                 "scheduled_at": reminder_time.strftime("%Y-%m-%d %H:%M:%S")
#             }
            
#             # Add to reminders list
#             self.redis.rpush("cart:reminders", json.dumps(reminder_data))
            
#             # Set reminder time as key for easy retrieval
#             self.redis.setex(
#                 f"cart:reminder:{user_id}:{order_id}", 
#                 int(delay_hours * 3600), 
#                 "1"
#             )
            
#             logger.info(f"Scheduled cart reminder for {user_id} (order {order_id}) in {delay_hours} hours")
#             return True
#         except Exception as e:
#             logger.error(f"Error scheduling cart reminder: {str(e)}")
#             return False

#     def get_pending_cart_reminders(self):
#         """Get all pending cart reminders"""
#         try:
#             reminders = []
#             all_reminders = self.redis.lrange("cart:reminders", 0, -1)
            
#             for reminder_str in all_reminders:
#                 # Decode if reminder_str is bytes
#                 if isinstance(reminder_str, bytes):
#                     reminder_str = reminder_str.decode('utf-8')
                
#                 reminder = json.loads(reminder_str)
#                 scheduled_at = datetime.strptime(reminder["scheduled_at"], "%Y-%m-%d %H:%M:%S")
                
#                 if datetime.now() >= scheduled_at:
#                     reminders.append(reminder)
            
#             return reminders
#         except Exception as e:
#             logger.error(f"Error getting pending cart reminders: {str(e)}")
#             return []

# # Initialize Redis state handler
# redis_state = RedisState()







# stateHandlers/redis_state.py
import redis
import json
from config.credentials import REDIS_URL
from utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger("redis_state")

class RedisState:
    def __init__(self):
        try:
            self.redis = redis.from_url(REDIS_URL)
            self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get_user_state(self, user_id):
        """Get user state from Redis"""
        try:
            state = self.redis.get(f"user:{user_id}:state")
            if state:
                # Decode if state is bytes
                if isinstance(state, bytes):
                    state = state.decode('utf-8')
                return json.loads(state)
            return None
        except Exception as e:
            logger.error(f"Error getting user state for {user_id}: {str(e)}")
            return None

    def set_user_state(self, user_id, state):
        """Set user state in Redis"""
        try:
            # Add timestamp for debugging
            state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.redis.setex(f"user:{user_id}:state", 3600, json.dumps(state))  # 1 hour expiry
            logger.debug(f"Set user state for {user_id}: {state}")
            return True
        except Exception as e:
            logger.error(f"Error setting user state for {user_id}: {str(e)}")
            return False

    def clear_user_state(self, user_id):
        """Clear user state from Redis"""
        try:
            self.redis.delete(f"user:{user_id}:state")
            logger.debug(f"Cleared user state for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing user state for {user_id}: {str(e)}")
            return False

    def get_cart(self, user_id):
        """Get user's cart from Redis"""
        try:
            cart = self.redis.get(f"user:{user_id}:cart")
            if cart:
                # Decode if cart is bytes
                if isinstance(cart, bytes):
                    cart = cart.decode('utf-8')
                cart_data = json.loads(cart)
                # Validate cart structure
                if "items" not in cart_data:
                    cart_data["items"] = []
                if "total" not in cart_data:
                    cart_data["total"] = 0
                return cart_data
            return {"items": [], "total": 0}
        except Exception as e:
            logger.error(f"Error getting cart for {user_id}: {str(e)}")
            return {"items": [], "total": 0}

    def add_to_cart(self, user_id, item_id, quantity=1):
        """Add item to user's cart using catalog item ID"""
        try:
            from config.settings import PRODUCT_CATALOG
            
            cart = self.get_cart(user_id)
            
            # Get product details from catalog
            product = PRODUCT_CATALOG.get(item_id)
            if not product:
                logger.error(f"Product ID {item_id} not found in catalog")
                return None
            
            # Check if item already in cart
            item_found = False
            for cart_item in cart["items"]:
                if cart_item["id"] == item_id:
                    cart_item["quantity"] += quantity
                    item_found = True
                    break
            
            if not item_found:
                cart["items"].append({
                    "id": item_id,
                    "name": product["name"],
                    "quantity": quantity,
                    "price": product["price"]
                })
            
            # Update total
            cart["total"] = sum(item["quantity"] * item["price"] for item in cart["items"])
            
            # Set expiry to 24 hours
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            logger.debug(f"Added {quantity}x {product['name']} (ID: {item_id}) to cart for {user_id}")
            return cart
        except Exception as e:
            logger.error(f"Error adding to cart for {user_id}: {str(e)}")
            return self.get_cart(user_id)

    def clear_cart(self, user_id):
        """Clear user's cart"""
        try:
            self.redis.delete(f"user:{user_id}:cart")
            logger.debug(f"Cleared cart for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing cart for {user_id}: {str(e)}")
            return False

    def set_branch(self, user_id, branch):
        """Set user's selected branch"""
        try:
            cart = self.get_cart(user_id)
            cart["branch"] = branch
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
            # Log branch selection
            logger.info(f"Branch set for {user_id}: {branch}")
            return True
        except Exception as e:
            logger.error(f"Error setting branch for {user_id}: {str(e)}")
            return False

    # def set_location(self, user_id, latitude, longitude):
    #     """Set user's location"""
    #     try:
    #         cart = self.get_cart(user_id)
    #         cart["location"] = {
    #             "latitude": latitude,
    #             "longitude": longitude,
    #         }
    #         self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
    #         # Log location
    #         logger.info(f"Location set for {user_id}: {latitude}, {longitude}")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error setting location for {user_id}: {str(e)}")
    #         return False

    def set_delivery_type(self, user_id, delivery_type):
        """Set user's delivery type (Delivery or Takeaway)"""
        try:
            cart = self.get_cart(user_id)
            cart["delivery_type"] = delivery_type
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
            # Log delivery type
            logger.info(f"Delivery type set for {user_id}: {delivery_type}")
            return True
        except Exception as e:
            logger.error(f"Error setting delivery type for {user_id}: {str(e)}")
            return False

    def set_payment_method(self, user_id, payment_method):
        """Set user's payment method"""
        try:
            cart = self.get_cart(user_id)
            cart["payment_method"] = payment_method
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
            # Log payment method
            logger.info(f"Payment method set for {user_id}: {payment_method}")
            return True
        except Exception as e:
            logger.error(f"Error setting payment method for {user_id}: {str(e)}")
            return False

    def create_order(self, order_data):
        """Create a new order in Redis"""
        try:
            order_id = order_data["order_id"]
            
            # Add to main orders list
            self.redis.rpush("orders:all", json.dumps(order_data))
            
            # Add to branch-specific list
            self.redis.rpush(f"orders:branch:{order_data['branch'].lower()}", json.dumps(order_data))
            
            # Set as active for 7 days
            self.redis.setex(f"order:{order_id}:active", 604800, "1")  # 7 days
            
            logger.info(f"Order {order_id} created in Redis")
            return True
        except Exception as e:
            logger.error(f"Error creating order in Redis: {str(e)}")
            return False

    def get_order(self, order_id):
        """Get order details from Redis"""
        try:
            # Check if order is active
            if not self.redis.exists(f"order:{order_id}:active"):
                return None
            
            # Search in all orders
            all_orders = self.redis.lrange("orders:all", 0, -1)
            for order_str in all_orders:
                # Decode if order_str is bytes
                if isinstance(order_str, bytes):
                    order_str = order_str.decode('utf-8')
                
                order = json.loads(order_str)
                if order["order_id"] == order_id:
                    return order
            
            return None
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            return None

    def update_order_status(self, order_id, status):
        """Update order status in Redis"""
        try:
            order = self.get_order(order_id)
            if not order:
                return False
            
            # Update status
            order["status"] = status
            order["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Remove old order
            order_json = json.dumps(order, sort_keys=True)
            self.redis.lrem("orders:all", 0, order_json)
            
            # Add updated order
            self.redis.rpush("orders:all", json.dumps(order))
            
            # Update in branch-specific list
            branch_list_key = f"orders:branch:{order['branch'].lower()}"
            self.redis.lrem(branch_list_key, 0, order_json)
            self.redis.rpush(branch_list_key, json.dumps(order))
            
            logger.info(f"Order {order_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {str(e)}")
            return False

    def archive_order(self, order_id):
        """Archive an order after delivery"""
        try:
            order = self.get_order(order_id)
            if not order:
                return False
            
            # Add to archive
            self.redis.rpush("orders:archive", json.dumps(order))
            
            # Remove from active lists
            order_json = json.dumps(order, sort_keys=True)
            self.redis.lrem("orders:all", 0, order_json)
            self.redis.lrem(f"orders:branch:{order['branch'].lower()}", 0, order_json)
            
            # Delete active flag
            self.redis.delete(f"order:{order_id}:active")
            
            logger.info(f"Order {order_id} archived successfully")
            return True
        except Exception as e:
            logger.error(f"Error archiving order {order_id}: {str(e)}")
            return False

    def schedule_cart_reminder(self, user_id, order_id, delay_hours=2):
        """Schedule a cart reminder"""
        try:
            reminder_time = datetime.now() + timedelta(hours=delay_hours)
            reminder_data = {
                "user_id": user_id,
                "order_id": order_id,
                "scheduled_at": reminder_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add to reminders list
            self.redis.rpush("cart:reminders", json.dumps(reminder_data))
            
            # Set reminder time as key for easy retrieval
            self.redis.setex(
                f"cart:reminder:{user_id}:{order_id}", 
                int(delay_hours * 3600), 
                "1"
            )
            
            logger.info(f"Scheduled cart reminder for {user_id} (order {order_id}) in {delay_hours} hours")
            return True
        except Exception as e:
            logger.error(f"Error scheduling cart reminder: {str(e)}")
            return False

    def get_pending_cart_reminders(self):
        """Get all pending cart reminders"""
        try:
            reminders = []
            all_reminders = self.redis.lrange("cart:reminders", 0, -1)
            
            for reminder_str in all_reminders:
                # Decode if reminder_str is bytes
                if isinstance(reminder_str, bytes):
                    reminder_str = reminder_str.decode('utf-8')
                
                reminder = json.loads(reminder_str)
                scheduled_at = datetime.strptime(reminder["scheduled_at"], "%Y-%m-%d %H:%M:%S")
                
                if datetime.now() >= scheduled_at:
                    reminders.append(reminder)
            
            return reminders
        except Exception as e:
            logger.error(f"Error getting pending cart reminders: {str(e)}")
            return []
    
    # def set_delivery_address(self, user_id, address):
    #     """Set user's delivery address"""
    #     try:
    #         cart = self.get_cart(user_id)
    #         cart["delivery_address"] = address
    #         self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
    #         # Log address
    #         logger.info(f"Delivery address set for {user_id}")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error setting delivery address for {user_id}: {str(e)}")
    #         return False
    
    def set_location(self, user_id, latitude, longitude):
        """Set user's location coordinates"""
        try:
            cart = self.get_cart(user_id)
            cart["location"] = {
                "latitude": latitude,
                "longitude": longitude
            }
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
            # Log location
            logger.info(f"Location coordinates set for {user_id}: {latitude}, {longitude}")
            return True
        except Exception as e:
            logger.error(f"Error setting location coordinates for {user_id}: {str(e)}")
            return False

    def set_delivery_address(self, user_id, address):
        """Set user's delivery address (text version)"""
        try:
            cart = self.get_cart(user_id)
            cart["delivery_address"] = address
            self.redis.setex(f"user:{user_id}:cart", 86400, json.dumps(cart))
            
            # Log address
            logger.info(f"Delivery address set for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting delivery address for {user_id}: {str(e)}")
            return False
    
    def get_complete_delivery_info(self, user_id):
        """Get complete delivery information including both text address and coordinates"""
        try:
            cart = self.get_cart(user_id)
            
            # Get text address
            text_address = cart.get("delivery_address", None)
            
            # Get location coordinates
            location = cart.get("location", None)
            
            # Create Google Maps link if coordinates exist
            maps_link = None
            if location and "latitude" in location and "longitude" in location:
                maps_link = f"https://www.google.com/maps?q={location['latitude']},{location['longitude']}"
            
            return {
                "text_address": text_address,
                "coordinates": location,
                "maps_link": maps_link
            }
        except Exception as e:
            logger.error(f"Error getting delivery info for {user_id}: {str(e)}")
            return {
                "text_address": None,
                "coordinates": None,
                "maps_link": None
            }

# Initialize Redis state handler
redis_state = RedisState()
