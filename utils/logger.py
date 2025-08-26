import logging
import os
from datetime import datetime

def get_c360_logger(name, level=logging.INFO, log_file=None, console=True):
    """Factory function to create and configure a logger for C360"""

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)

        if log_file is None:
            log_file = f"logs/{name}_{datetime.now().strftime('%Y%m%d')}.log"

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    return logger

