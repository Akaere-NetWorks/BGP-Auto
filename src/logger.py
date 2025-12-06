"""Logging module"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """Logger class for console and file output"""
    
    def __init__(self, log_dir: Path = None, name: str = "BGP-Auto"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logs = []  # Store all log messages
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_dir:
            # Clear log directory
            if log_dir.exists():
                import shutil
                shutil.rmtree(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / "bgp-auto.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            self.log_file = log_file
        else:
            self.log_file = None
    
    def info(self, message: str):
        """Log info message"""
        self.logs.append(('INFO', message))
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logs.append(('ERROR', message))
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logs.append(('WARNING', message))
        self.logger.warning(message)
    
    def success(self, message: str):
        """Log success message"""
        self.logs.append(('SUCCESS', f"✓ {message}"))
        self.logger.info(f"✓ {message}")
    
    def get_logs(self):
        """Get all logged messages"""
        return self.logs
