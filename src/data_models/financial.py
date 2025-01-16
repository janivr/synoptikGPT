import pandas as pd
from typing import Dict, Any

class FinancialModel:
    def __init__(self, file_path: str):
        self.data = self.load_and_validate_data(file_path)
        self.metadata = self.generate_metadata()

    def load_and_validate_data(self, file_path: str) -> pd.DataFrame:
        financial_df = pd.read_csv(file_path)

        # Validate required columns
        required_columns = [
            'Building ID', 'Date', 'Lease Cost (USD)', 'Total Operating Expense (USD)', 'Energy Costs (USD)',
            'Utilities Costs (USD)', 'Maintenance Costs (USD)', 'Catering Costs (USD)', 'Cleaning Costs (USD)',
            'Security Costs (USD)', 'Insurance Costs (USD)', 'Waste Disposal Costs (USD)', 'Other Costs (USD)'
        ]
        missing_columns = [col for col in required_columns if col not in financial_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Validate data types
        financial_df['Building ID'] = financial_df['Building ID'].astype(str)
        financial_df['Date'] = pd.to_datetime(financial_df['Date'])

        for col in required_columns[2:]:
            financial_df[col] = financial_df[col].astype(int)

        return financial_df

    def generate_metadata(self) -> Dict[str, Any]:
        return {
            "columns": list(self.data.columns),
            "buildings": self.data['Building ID'].unique(),
            "date_range": {
                "min": self.data['Date'].min(),
                "max": self.data['Date'].max()
            }
        }

    def get_building_financials(self, building_id: str) -> pd.DataFrame:
        return self.data[self.data['Building ID'] == building_id]