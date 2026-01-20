"""
Structured logging configuration for the application.
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from app.middleware.request_id import get_request_id


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log messages.
    Includes timestamp, level, request ID, and message.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Get request ID from context
        request_id = get_request_id() or "N/A"
        
        # Build structured log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "request_id": request_id,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Format as key=value pairs for easy parsing
        return " ".join([f"{k}={v}" for k, v in log_data.items()])


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(StructuredFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Reduce noise
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce DB query logs


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Security-specific logging functions
def log_security_event(event_type: str, details: Dict[str, Any], user_id: int = None) -> None:
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event (e.g., "login_failed", "token_invalid")
        details: Additional event details
        user_id: User ID if applicable
    """
    logger = get_logger("security")
    request_id = get_request_id() or "N/A"
    
    log_message = f"SECURITY_EVENT type={event_type} request_id={request_id}"
    if user_id:
        log_message += f" user_id={user_id}"
    
    for key, value in details.items():
        log_message += f" {key}={value}"
    
    logger.warning(log_message)


def log_data_access(resource_type: str, resource_id: Any, user_id: int, action: str) -> None:
    """
    Log data access for audit trail.
    
    Args:
        resource_type: Type of resource (e.g., "trade", "journal")
        resource_id: Resource identifier
        user_id: User performing the action
        action: Action performed (e.g., "read", "create", "update", "delete")
    """
    logger = get_logger("audit")
    request_id = get_request_id() or "N/A"
    
    logger.info(
        f"DATA_ACCESS resource_type={resource_type} resource_id={resource_id} "
        f"user_id={user_id} action={action} request_id={request_id}"
    )
