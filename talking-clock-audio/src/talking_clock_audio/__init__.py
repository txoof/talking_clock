# src/talking_clock_audio/__init__.py

"""Talking Clock Audio - Generate multilingual time phrase audio files.

This package provides tools for generating audio files from text phrases
using Piper TTS voices in multiple languages. Designed for creating
accessible talking clock applications.
"""

import logging
import sys

__version__ = "0.1.0"


def setup_logging(level: str = 'WARNING', log_file: str | None = None) -> None:
    """Configure logging for the talking_clock_audio package.
    
    Sets up console logging with optional file output. Uses a standardized
    format with timestamps and log levels.
    
    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to WARNING.
        log_file: Optional path to write logs to file. If None, only logs
            to console (stderr).
    
    Example:
        >>> setup_logging(level='INFO')
        >>> setup_logging(level='DEBUG', log_file='app.log')
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    
    # Get root logger for our package
    logger = logging.getLogger('talking_clock_audio')
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with readable format
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
