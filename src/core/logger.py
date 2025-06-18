import logging
import sys

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("app_logger")

def get_logger(name: str = "app_logger"):
    """
    Returns a logger instance.
    """
    return logging.getLogger(name)