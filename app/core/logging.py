import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def setup_logging():
    """Configure logging for production environment"""
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create a rotating file handler
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set logging level for specific modules
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING) 