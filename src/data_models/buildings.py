import pandas as pd
from typing import Dict, Any

class BuildingsModel:
    def __init__(self, file_path: str):
        self.data = self.load_and_validate_data(file_path)
        self.metadata = self.generate_metadata()

    def load_and_validate_data(self, file_path: str) -> pd.DataFrame:
        buildings_df = pd.read_csv(file_path)

        # Validate required columns
        required_columns = [
            'Building ID', 'Location', 'Size', 'Purpose', 'Ownership', 'Year Built', 'LEED Certified'
        ]
        missing_columns = [col for col in required_columns if col not in buildings_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Validate data types
        buildings_df['Building ID'] = buildings_df['Building ID'].astype(str)
        buildings_df['Size'] = buildings_df['Size'].astype(int)
        buildings_df['Year Built'] = buildings_df['Year Built'].astype(int)

        return buildings_df

    def generate_metadata(self) -> Dict[str, Any]:
        return {
            "columns": list(self.data.columns),
            "size_range": {
                "min": self.data['Size'].min(),
                "max": self.data['Size'].max()
            },
            "year_range": {
                "min": self.data['Year Built'].min(),
                "max": self.data['Year Built'].max()
            },
            "location_count": self.data['Location'].nunique(),
            "purpose_count": self.data['Purpose'].nunique(),
            "ownership_count": self.data['Ownership'].nunique(),
            "leed_certified_count": self.data['LEED Certified'].str.lower().eq('checked').sum()
        }

    def filter_buildings(self, criteria: Dict[str, Any]) -> pd.DataFrame:
        filtered_data = self.data.copy()

        if 'location' in criteria:
            filtered_data = filtered_data[filtered_data['Location'].str.contains(criteria['location'], case=False)]

        if 'min_size' in criteria and 'max_size' in criteria:
            filtered_data = filtered_data[(filtered_data['Size'] >= criteria['min_size']) & (filtered_data['Size'] <= criteria['max_size'])]

        if 'ownership_type' in criteria:
            filtered_data = filtered_data[filtered_data['Ownership'] == criteria['ownership_type']]

        if 'purpose' in criteria:
            filtered_data = filtered_data[filtered_data['Purpose'].str.contains(criteria['purpose'], case=False)]

        if 'leed_certified' in criteria:
            filtered_data = filtered_data[filtered_data['LEED Certified'].str.lower().eq(str(criteria['leed_certified']).lower())]

        return filtered_data