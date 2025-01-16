# Import key classes to make them easily accessible
from .buildings import BuildingsModule
from .financial import FinancialModule

# Define what gets imported with `from modules import *`
__all__ = ['BuildingsModule', 'FinancialModule']

# Optional: Package-level logging or initialization
import logging
logger = logging.getLogger(__name__)
logger.info("Real Estate Modules Package Initialized")

# Optional: Version information
__version__ = '0.1.0'