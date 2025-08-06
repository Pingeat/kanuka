# # utils/logger.py
# import logging
# from config.settings import Settings

# def get_logger(name: str):
#     """Configure and return logger instance"""
#     logger = logging.getLogger(name)
    
#     if not logger.handlers:
#         logger.setLevel(logging.INFO)
        
#         formatter = logging.Formatter(
#             '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#         )
        
#         # Console handler
#         ch = logging.StreamHandler()
#         ch.setFormatter(formatter)
#         logger.addHandler(ch)
        
#         # File handler (optional)
#         # fh = logging.FileHandler('app.log')
#         # fh.setFormatter(formatter)
#         # logger.addHandler(fh)
    
#     return logger





# utils/logger.py
import logging
from datetime import datetime

def get_logger(name):
    """Configure and return a logger"""
    logger = logging.getLogger(name)
    
    # Only add handler if it doesn't already have one
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger