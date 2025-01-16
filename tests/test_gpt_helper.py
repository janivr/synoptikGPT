from src.utils.data_loader import DataLoader
from src.modules.buildings import BuildingsModule
from src.modules.financial import FinancialModule
from src.utils.gpt_helper import ask_gpt

def test_gpt_responses():
    # Load test data
    buildings_df = DataLoader.load_buildings_data()
    financial_df = DataLoader.load_financial_data()
    
    # Initialize modules
    buildings_module = BuildingsModule(buildings_df)
    financial_module = FinancialModule(financial_df)
    
    # Test cases
    test_queries = [
        "Which building has the highest capacity?",
        "What is the oldest building?",
        "How many buildings are LEED certified?",
        "Show me the monthly utility costs for B002 in 2023",
        "Which building has the highest energy target?"
    ]
    
    # Run tests
    print("Running GPT response tests...\n")
    for query in test_queries:
        print(f"Query: {query}")
        messages = [{"role": "user", "content": query}]
        
        try:
            response = ask_gpt(messages, buildings_module, financial_module)
            print(f"Response: {response}\n")
            print("-" * 80 + "\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")
            print("-" * 80 + "\n")

if __name__ == "__main__":
    test_gpt_responses()