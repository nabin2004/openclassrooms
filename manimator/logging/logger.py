import logging
from typing import Any, Optional
from enum import Enum
from datetime import datetime
from manimator.contracts.validation import ErrorType


class ManimatorLogLevel(Enum):
    """Custom log levels for Manimator operations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ManimatorException(logging.Logger):
    """
    A comprehensive exception class for Manimator that combines logging and error handling.
    
    This class extends Python's logging.Logger to provide integrated exception handling
    with detailed logging capabilities for the Manimator animation generation pipeline.
    """
    
    def __init__(self, name: str, error_type: Optional[ErrorType] = None, 
                 scene_id: Optional[int] = None, error_message: Optional[str] = None,
                 error_line: Optional[int] = None, failing_code: Optional[str] = None):
        """
        Initialize ManimatorException with logging and error details.
        
        Args:
            name: Logger name (typically the module or component name)
            error_type: Type of error from ErrorType enum
            scene_id: ID of the scene where error occurred
            error_message: Human-readable error message
            error_line: Line number where error occurred
            failing_code: The code that caused the error
        """
        super().__init__(name, logging.DEBUG)
        
        # Error attributes
        self.error_type = error_type
        self.scene_id = scene_id
        self.error_message = error_message
        self.error_line = error_line
        self.failing_code = failing_code
        self.timestamp = datetime.now().isoformat()
        
        # Configure logger if not already configured
        if not self.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with appropriate handlers and formatters."""
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Create formatter with detailed error information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.addHandler(console_handler)
        self.setLevel(logging.DEBUG)
    
    def log_error(self, message: str, level: ManimatorLogLevel = ManimatorLogLevel.ERROR, 
                  extra_data: Optional[dict] = None):
        """
        Log an error with detailed context.
        
        Args:
            message: Error message to log
            level: Log level for the message
            extra_data: Additional context data to include in log
        """
        log_message = self._format_log_message(message, extra_data)
        
        if level == ManimatorLogLevel.DEBUG:
            self.debug(log_message)
        elif level == ManimatorLogLevel.INFO:
            self.info(log_message)
        elif level == ManimatorLogLevel.WARNING:
            self.warning(log_message)
        elif level == ManimatorLogLevel.ERROR:
            self.error(log_message)
        elif level == ManimatorLogLevel.CRITICAL:
            self.critical(log_message)
    
    def _format_log_message(self, message: str, extra_data: Optional[dict] = None) -> str:
        """Format log message with error context."""
        context_parts = [message]
        
        if self.error_type:
            context_parts.append(f"Error Type: {self.error_type.value}")
        
        if self.scene_id is not None:
            context_parts.append(f"Scene ID: {self.scene_id}")
        
        if self.error_line is not None:
            context_parts.append(f"Line: {self.error_line}")
        
        if extra_data:
            for key, value in extra_data.items():
                context_parts.append(f"{key}: {value}")
        
        return " | ".join(context_parts)
    
    def raise_with_logging(self, message: Optional[str] = None, 
                          level: ManimatorLogLevel = ManimatorLogLevel.ERROR):
        """
        Log the error and raise the exception.
        
        Args:
            message: Custom error message (uses stored message if None)
            level: Log level for the error
        """
        error_msg = message or self.error_message or "ManimatorException occurred"
        self.log_error(error_msg, level)
        raise Exception(error_msg)
    
    def get_error_summary(self) -> dict:
        """
        Get a comprehensive summary of the error.
        
        Returns:
            Dictionary containing all error details
        """
        return {
            "timestamp": self.timestamp,
            "logger_name": self.name,
            "error_type": self.error_type.value if self.error_type else None,
            "scene_id": self.scene_id,
            "error_message": self.error_message,
            "error_line": self.error_line,
            "failing_code": self.failing_code,
        }
    
    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [f"ManimatorException({self.name})"]
        
        if self.error_type:
            parts.append(f"Type: {self.error_type.value}")
        
        if self.scene_id is not None:
            parts.append(f"Scene: {self.scene_id}")
        
        if self.error_message:
            parts.append(f"Message: {self.error_message}")
        
        if self.error_line is not None:
            parts.append(f"Line: {self.error_line}")
        
        return " - ".join(parts)
    
    def __repr__(self) -> str:
        """Detailed string representation of the exception."""
        return (f"ManimatorException(name='{self.name}', error_type={self.error_type}, "
                f"scene_id={self.scene_id}, error_message='{self.error_message}', "
                f"error_line={self.error_line})") 
