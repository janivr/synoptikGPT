import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Optional

class BuildingsModule:
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the Buildings Module with comprehensive data processing
        
        :param dataframe: DataFrame containing building information
        """
        self._validate_dataframe(dataframe)
        self.data = dataframe
        self._preprocess_data()
    
    def _validate_dataframe(self, dataframe: pd.DataFrame):
        """
        Comprehensive data validation for buildings DataFrame
        
        :param dataframe: DataFrame to validate
        :raises ValueError: If DataFrame is invalid
        """
        required_columns = [
            'Building ID', 'Location', 'Size', 'Purpose', 
            'Ownership', 'Year Built', 'LEED Certified'
        ]
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Validate key columns
        if not pd.api.types.is_string_dtype(dataframe['Building ID']):
            raise ValueError("Building ID must be a string")
        
        if not pd.api.types.is_numeric_dtype(dataframe['Size']):
            raise ValueError("Size must be numeric")
        
        if not pd.api.types.is_numeric_dtype(dataframe['Year Built']):
            raise ValueError("Year Built must be numeric")
    
    def _preprocess_data(self):
        """
        Preprocess and enrich building data
        """
        # Standardize location
        self.data['Location'] = self.data['Location'].str.title()
        
        # Categorize building sizes
        self.data['Size Category'] = pd.cut(
            self.data['Size'], 
            bins=[0, 10000, 50000, 100000, np.inf], 
            labels=['Small', 'Medium', 'Large', 'Very Large']
        )
        
        # Age calculation
        current_year = pd.Timestamp.now().year
        self.data['Building Age'] = current_year - self.data['Year Built']
        
        # Ownership type standardization
        self.data['Ownership Type'] = self.data['Ownership'].apply(self._categorize_ownership)
    
    def _categorize_ownership(self, ownership: str) -> str:
        """
        Categorize ownership types
        
        :param ownership: Raw ownership string
        :return: Standardized ownership category
        """
        ownership = str(ownership).lower()
        categories = {
            'corporate': 'Corporate',
            'reit': 'REIT',
            'private': 'Private',
            'government': 'Government',
            'institutional': 'Institutional'
        }
        
        for key, category in categories.items():
            if key in ownership:
                return category
        
        return 'Other'
    
    def get_portfolio_overview(self) -> Dict[str, Any]:
        """
        Generate comprehensive portfolio overview
        
        :return: Dictionary of portfolio-wide insights
        """
        
       # Convert 'LEED Certified' to boolean
        self.data['LEED Certified'] = self.data['LEED Certified'].fillna('').astype(str).str.lower() == 'checked'
    

        return {
            'total_buildings': len(self.data),
            'total_portfolio_size': self.data['Size'].sum(),
            'avg_building_size': self.data['Size'].mean(),
            'size_distribution': dict(self.data['Size Category'].value_counts()),
            'ownership_breakdown': dict(self.data['Ownership Type'].value_counts()),
            'location_distribution': dict(self.data['Location'].value_counts()),
            'leed_certified_percentage': (self.data['LEED Certified'].sum() / len(self.data)) * 100,
            'age_statistics': {
                'avg_age': self.data['Building Age'].mean(),
                'youngest': self.data['Building Age'].min(),
                'oldest': self.data['Building Age'].max()
            }
        }
    
    def find_buildings(self, criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Advanced building search with multiple criteria
        
        :param criteria: Dictionary of search criteria
        :return: Filtered DataFrame of matching buildings
        """
        filtered_data = self.data.copy()
        
        # Location filtering
        if 'location' in criteria:
            filtered_data = filtered_data[
                filtered_data['Location'].str.contains(criteria['location'], case=False)
            ]
        
        # Size range filtering
        if 'min_size' in criteria and 'max_size' in criteria:
            filtered_data = filtered_data[
                (filtered_data['Size'] >= criteria['min_size']) & 
                (filtered_data['Size'] <= criteria['max_size'])
            ]
        
        # Ownership type filtering
        if 'ownership_type' in criteria:
            filtered_data = filtered_data[
                filtered_data['Ownership Type'] == criteria['ownership_type']
            ]
        
        # Purpose filtering
        if 'purpose' in criteria:
            filtered_data = filtered_data[
                filtered_data['Purpose'].str.contains(criteria['purpose'], case=False)
            ]
        
        # LEED certification filtering
        if 'leed_certified' in criteria:
            filtered_data = filtered_data[
                filtered_data['LEED Certified'] == criteria['leed_certified']
            ]
        
        return filtered_data
    
    def generate_building_profile(self, building_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate detailed profile for a specific building
        
        :param building_id: Unique identifier for the building
        :return: Comprehensive building profile or None
        """
        building = self.data[self.data['Building ID'] == building_id]
        
        if building.empty:
            return None
        
        building_row = building.iloc[0]
        
        return {
            'id': building_row['Building ID'],
            'location_details': {
                'full_address': building_row['Location'],
                'city': building_row['Location'].split(',')[0] if ',' in str(building_row['Location']) else building_row['Location']
            },
            'physical_characteristics': {
                'total_size': f"{building_row['Size']:,} sq ft",
                'size_category': building_row['Size Category'],
                'year_built': building_row['Year Built'],
                'age': building_row['Building Age']
            },
            'operational_details': {
                'purpose': building_row['Purpose'],
                'ownership_type': building_row['Ownership Type'],
                'leed_certified': building_row['LEED Certified']
            },
            'additional_insights': self._generate_contextual_insights(building_row)
        }
    
    def _generate_contextual_insights(self, building_row: pd.Series) -> Dict[str, str]:
        """
        Generate contextual insights for a specific building
        
        :param building_row: Single row of building data
        :return: Dictionary of contextual insights
        """
        insights = {}
        
        # Size context
        avg_size = self.data['Size'].mean()
        if building_row['Size'] > avg_size * 1.5:
            insights['size_note'] = "Significantly larger than portfolio average"
        elif building_row['Size'] < avg_size * 0.5:
            insights['size_note'] = "Considerably smaller than portfolio average"
        
        # Age context
        avg_age = self.data['Building Age'].mean()
        if building_row['Building Age'] > avg_age * 1.5:
            insights['age_note'] = "Older than typical portfolio building"
        elif building_row['Building Age'] < avg_age * 0.5:
            insights['age_note'] = "Newer than typical portfolio building"
        
        return insights