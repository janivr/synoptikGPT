import pytest
from src.modules.buildings import BuildingsModule

def test_buildings_module_summary_stats(sample_buildings_df):
    """
    Test summary statistics generation for buildings
    """
    buildings_module = BuildingsModule(sample_buildings_df)
    stats = buildings_module.get_summary_stats()
    
    assert stats['total_buildings'] == 3
    assert stats['regions'] == {}  # No region column in sample data
    assert stats['ownership_types'] == {'Corporate': 1, 'Private': 1, 'REIT': 1}
    assert stats['leed_certified'] == 2

def test_buildings_module_query_processing(sample_buildings_df):
    """
    Test query processing for specific building
    """
    buildings_module = BuildingsModule(sample_buildings_df)
    
    # Test valid building query
    result = buildings_module.process_query("Tell me about B001")
    assert result is not None
    assert result['building_id'] == 'B001'
    assert result['details']['Location'] == 'New York'
    
    # Test invalid building query
    result = buildings_module.process_query("Tell me about B999")
    assert result is None