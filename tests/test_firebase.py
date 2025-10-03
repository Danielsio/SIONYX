import sys
from pathlib import Path

# Add src to path for importing
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

# Initialize logging using the centralized system
from utils.logger import SionyxLogger, get_logger
import logging

# Setup logging for tests
SionyxLogger.setup(log_level=logging.INFO, log_to_file=False)
logger = get_logger(__name__)

from services.firebase_client import FirebaseClient

client = FirebaseClient()
logger.info("Firebase client created successfully!")
logger.info(f"Database URL: {client.database_url}")