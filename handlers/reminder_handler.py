# handlers/reminder_handler.py
import json
import os
from config.settings import DAILY_REMINDER_TIME
from services.whatsapp_service import send_cart_reminder
from stateHandlers.redis_state import redis_state
from utils.logger import get_logger
from datetime import datetime, time, timedelta
import threading
import time as time_module

from utils.time_utils import get_current_ist

logger = get_logger("reminder_handler")
BRAND_ID = os.getenv("BRAND_ID", "default").lower()

def process_cart_reminders():
    """Process pending cart reminders"""
    logger.info("Processing cart reminders")
    
    # Get all pending reminders
    reminders = redis_state.get_pending_cart_reminders()
    
    for reminder in reminders:
        user_id = reminder["user_id"]
        order_id = reminder["order_id"]
        
        # Send reminder
        # send_cart_reminder(user_id, order_id)
        
        # Log reminder
        from utils.csv_utils import log_cart_reminder
        log_cart_reminder(user_id, order_id)
        
        # Remove from pending reminders
        redis_state.redis.lrem(
            f"cart:{BRAND_ID}:reminders", 0, json.dumps(reminder)
        )
    
    logger.info(f"Processed {len(reminders)} cart reminders")

def schedule_daily_tasks():
    """Schedule daily tasks to run at specific times"""
    logger.info("Starting daily tasks scheduler")
    
    # Run continuously
    while True:
        now = get_current_ist()
        
        # Process cart reminders every 15 minutes
        if now.minute % 15 == 0:
            process_cart_reminders()
        
        # Daily reminder at specified time
        daily_reminder_time = datetime.strptime(DAILY_REMINDER_TIME, "%H:%M").time()
        if now.time() >= daily_reminder_time and now.time() < (datetime.combine(now.date(), daily_reminder_time) + timedelta(minutes=1)).time():
            # This would send daily reminders to users with items in cart
            logger.info("Sending daily reminders")
        
        # Sleep for 1 minute before checking again
        time_module.sleep(60)

def start_scheduler():
    """Start the scheduler in a separate thread"""
    scheduler_thread = threading.Thread(target=schedule_daily_tasks, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler started")