from src.utils.data_loader import DataLoader
from src.modules.buildings import BuildingsModule
from src.modules.financial import FinancialModule
from src.utils.gpt_helper import ask_gpt

def run_test_query(query: str, buildings_module, financial_module):
    """Helper function to run a test query"""
    messages = [{"role": "user", "content": query}]
    response = ask_gpt(messages, buildings_module, financial_module)
    print(f"\nQuery: {query}")
    print(f"Response: {response}")
    print("-" * 80)

def test_error_cases():
    """Test error handling"""
    buildings_df = DataLoader.load_buildings_data()
    financial_df = DataLoader.load_financial_data()
    
    buildings_module = BuildingsModule(buildings_df)
    financial_module = FinancialModule(financial_df)
    
    # Test invalid building ID
    print("\nTesting invalid building ID:")
    run_test_query("Show me utility costs for B999 in 2023", buildings_module, financial_module)
    
    # Test invalid year
    print("\nTesting invalid year:")
    run_test_query("Show me utility costs for B002 in 2030", buildings_module, financial_module)
    
    # Test missing data
    print("\nTesting missing data query:")
    run_test_query("Show me utility costs", buildings_module, financial_module)

def test_valid_queries():
    """Test valid queries"""
    buildings_df = DataLoader.load_buildings_data()
    financial_df = DataLoader.load_financial_data()
    
    buildings_module = BuildingsModule(buildings_df)
    financial_module = FinancialModule(financial_df)
    
    # Test utility costs
    print("\nTesting valid utility costs query:")
    run_test_query("Show me utility costs for B002 in 2023", buildings_module, financial_module)
    
    # Test building capacity
    print("\nTesting building capacity query:")
    run_test_query("Which building has the highest capacity?", buildings_module, financial_module)
    
    # Test LEED certification
    print("\nTesting LEED certification query:")
    run_test_query("How many buildings are LEED certified?", buildings_module, financial_module)

if __name__ == "__main__":
    print("Running error case tests...")
    test_error_cases()
    
    print("\nRunning valid query tests...")
    test_valid_queries()