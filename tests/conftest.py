import pytest
import pandas as pd
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_buildings_df():
    """
    Fixture to provide a sample buildings DataFrame for testing
    """
    return pd.DataFrame({
        'Building ID': ['B001', 'B002', 'B003'],
        'Location': ['New York', 'Chicago', 'San Francisco'],
        'Size': [50000, 75000, 60000],
        'Purpose': ['Office', 'Retail', 'Mixed-Use'],
        'Ownership': ['Corporate', 'Private', 'REIT'],
        'LEED Certified': [True, False, True]
    })

@pytest.fixture
def sample_financial_df():
    """
    Fixture to provide a sample financial DataFrame for testing
    """
    return pd.DataFrame({
        'Building ID': ['B001', 'B001', 'B002'],
        'Date': pd.date_range(start='2023-01-01', periods=3),
        'Total Operating Expense (USD)': [100000, 105000, 95000],
        'Energy Costs (USD)': [20000, 22000, 18000],
        'Cleaning Costs (USD)': [5000, 5500, 4500],
        'Utilities Costs (USD)': [15000, 16000, 14000],
        'Maintenance Costs (USD)': [10000, 11500, 9500]
    })