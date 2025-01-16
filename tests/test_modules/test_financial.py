import pytest
from src.modules.financial import FinancialModule

def test_financial_module_summary_stats(sample_financial_df):
    """
    Test financial summary statistics generation
    """
    financial_module = FinancialModule(sample_financial_df)
    stats = financial_module.get_summary_stats()
    
    assert stats['total_operating_expenses'] == 300000
    assert 'expense_by_category' in stats
    assert len(stats['date_range']) == 2

def test_financial_query_processing(sample_financial_df):
    """
    Test financial query processing
    """
    financial_module = FinancialModule(sample_financial_df)
    
    # Test yearly query
    result = financial_module.process_financial_query("Financial data for B001 in 2023")
    assert result is not None
    assert 'yearly_total' in result
    assert 'monthly_data' in result