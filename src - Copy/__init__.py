# Top-level package initialization
import logging
import sys

# Configure logging for the entire project
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('synoptik_gpt.log')
    ]
)

# Optional: Version and metadata
__version__ = '0.1.0'
__author__ = ' Janiv Ratson'
__description__ = 'Real Estate Portfolio Management Assistant'

# Optional: Centralized configuration
from dotenv import load_dotenv
load_dotenv()  # Load environment variables

# Optional: Validate critical dependencies
def check_dependencies():
    """
    Check if all required dependencies are installed
    """
    try:
        import pandas
        import streamlit
        import openai
    except ImportError as e:
        logging.error(f"Missing critical dependency: {e}")
        sys.exit(1)

# Run dependency check when package is imported
check_dependencies()
