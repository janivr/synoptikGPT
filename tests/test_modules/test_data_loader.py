import pytest
import pandas as pd
from src.utils.data_loader import DataLoader
import os

def test_data_loader_buildings(tmp_path):
    """
    Test data loading for buildings
    """
    # Create a temporary CSV file
    sample_data = pd.DataFrame({
        'Building ID': ['B001', 'B002'],
        'Location': ['New York', 'Chicago']
    })
    csv_path = tmp_path / "test_buildings.csv"
    sample_data.to_csv(csv_path, index=False)
    
    # Load data
    df = DataLoader.load_data(csv_path)
    
    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == ['Building ID', 'Location']