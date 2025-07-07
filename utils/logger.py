import logging
import sys

# Create a custom logger
logger = logging.getLogger("agentic_sales_agent")
logger.setLevel(logging.INFO)

# Avoid duplicate log handlers if re-imported
if not logger.handlers:

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)
