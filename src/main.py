import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.data_loader import DataLoader
from modules.buildings_module import BuildingsModule
from modules.financial_module import FinancialModule
from cli.streamlit_app import run_streamlit_app

def main():
    """
    Central application entry point
    Demonstrates how different modules can be initialized and used
    """
    try:
        # Load data
        buildings_df = DataLoader.load_buildings_data()
        financial_df = DataLoader.load_financial_data()

        # Initialize modules
        buildings_module = BuildingsModule(buildings_df)
        financial_module = FinancialModule(financial_df)

        # Example of module usage
        portfolio_overview = buildings_module.get_portfolio_overview()
        print("Portfolio Overview:")
        print(portfolio_overview)

        financial_overview = financial_module.get_financial_overview()
        print("\nFinancial Overview:")
        print(financial_overview)

        # Optional: Run Streamlit app
        run_streamlit_app(buildings_module, financial_module)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()