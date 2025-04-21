import logging
import sys
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler

from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for logs with additional fields
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = settings.PROJECT_NAME
        
        # Add trace ID if available from context
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id

def setup_logging() -> logging.Logger:
    """
    Configure logging for the application
    
    Returns:
        Logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(log_level)
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            filename="logs/app.log", 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        handlers.append(file_handler)
    except Exception as e:
        # If log directory doesn't exist, just log to console
        print(f"Warning: Could not create file handler: {e}")
    
    # Set formatter based on configuration
    if settings.LOG_FORMAT.lower() == "json":
        # JSON formatter
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Text formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Add formatter to handlers
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger