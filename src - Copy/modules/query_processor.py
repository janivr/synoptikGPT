import re
from typing import Dict, Optional
import pandas as pd
from datetime import datetime

class QueryProcessor:
    def __init__(self, buildings_module, financial_module):
        self.buildings_df = buildings_module.data
        self.financial_df = financial_module.data
        self.current_year = 2025  # From system context
        
    def process_query(self, query: str) -> Dict:
        """Main query processing method that routes to specific handlers"""
        query = query.lower()
        
        # Try all query handlers and use the first one that returns a result
        handlers = [
            self._handle_building_metrics,
            self._handle_financial_metrics,
            self._handle_building_counts,
            self._handle_time_based_queries,
            self._handle_location_queries,
            self._handle_comparison_queries
        ]
        
        for handler in handlers:
            result = handler(query)
            if result:
                return self._validate_result(result)
                
        return {"error": "Could not process query"}

    def _handle_building_metrics(self, query: str) -> Optional[Dict]:
        """Handle queries about building characteristics"""
        result = {}
        
        # Capacity queries
        if "capacity" in query:
            if any(word in query for word in ["highest", "most", "maximum", "largest"]):
                row = self.buildings_df.loc[self.buildings_df['Employee Capacity'].idxmax()]
                result = {
                    'type': 'capacity',
                    'subtype': 'highest',
                    'data': row.to_dict(),
                    'metric': row['Employee Capacity']
                }
            elif any(word in query for word in ["lowest", "least", "minimum", "smallest"]):
                row = self.buildings_df.loc[self.buildings_df['Employee Capacity'].idxmin()]
                result = {
                    'type': 'capacity',
                    'subtype': 'lowest',
                    'data': row.to_dict(),
                    'metric': row['Employee Capacity']
                }

        # Energy target queries
        elif "energy target" in query:
            if any(word in query for word in ["highest", "most", "maximum"]):
                row = self.buildings_df.loc[self.buildings_df['Energy Target (kWh/sqft/yr)'].idxmax()]
                result = {
                    'type': 'energy_target',
                    'subtype': 'highest',
                    'data': row.to_dict(),
                    'metric': row['Energy Target (kWh/sqft/yr)']
                }

        # Size queries
        elif any(word in query for word in ["size", "square feet", "sqft"]):
            if any(word in query for word in ["highest", "most", "maximum", "largest"]):
                row = self.buildings_df.loc[self.buildings_df['Size'].idxmax()]
                result = {
                    'type': 'size',
                    'subtype': 'highest',
                    'data': row.to_dict(),
                    'metric': row['Size']
                }

        return result if result else None

    def _handle_financial_metrics(self, query: str) -> Optional[Dict]:
        """Handle queries about financial metrics"""
        result = {}
        
        # Extract building ID if present
        building_match = re.search(r'B\d{3}', query)
        building_id = building_match.group(0) if building_match else None
        
        # Extract year if present
        year_match = re.search(r'\b20\d{2}\b', query)
        year = int(year_match.group(0)) if year_match else None
        
        # Utility costs
        if "utility" in query and "cost" in query:
            # Initialize with complete dataset
            filtered_df = self.financial_df.copy()
            
            # Validate and filter by building ID
            if building_id:
                if building_id not in filtered_df['Building ID'].unique():
                    return {
                        'type': 'utility_costs',
                        'error': f"Building {building_id} not found in the database"
                    }
                filtered_df = filtered_df[filtered_df['Building ID'] == building_id]
            
            # Validate and filter by year
            if year:
                filtered_df['year'] = pd.to_datetime(filtered_df['Date']).dt.year
                if year not in filtered_df['year'].unique():
                    return {
                        'type': 'utility_costs',
                        'error': f"No utility cost data available for {year}"
                    }
                filtered_df = filtered_df[filtered_df['year'] == year]
            
            # Group by month and calculate costs
            filtered_df['month'] = pd.to_datetime(filtered_df['Date']).dt.month
            monthly_costs = filtered_df.groupby('month')['Utilities Costs (USD)'].sum()
            
            if monthly_costs.empty:
                return {
                    'type': 'utility_costs',
                    'error': 'No utility costs data found for the specified criteria'
                }
            
            return {
                'type': 'utility_costs',
                'building_id': building_id,
                'year': year,
                'data': monthly_costs.to_dict()
            }

        # Operating expenses
        elif "operating expense" in query:
            if "total" in query or "all buildings" in query:
                total = self.buildings_df['Total Operating Expense (2024)'].sum()
                result = {
                    'type': 'operating_expense',
                    'subtype': 'total',
                    'year': 2024,
                    'amount': total
                }

        return result if result else None

    def _handle_building_counts(self, query: str) -> Optional[Dict]:
        """Handle queries about building counts"""
        result = {}
        
        if "how many" in query or "number of" in query:
            if "leed" in query:
                count = len(self.buildings_df[self.buildings_df['LEED Certified'] == 'checked'])
                result = {
                    'type': 'count',
                    'subtype': 'leed',
                    'count': count
                }
            elif "lease" in query or "owned" in query:
                lease_count = len(self.buildings_df[self.buildings_df['Ownership'] == 'Lease'])
                own_count = len(self.buildings_df[self.buildings_df['Ownership'] == 'Own'])
                result = {
                    'type': 'count',
                    'subtype': 'ownership',
                    'lease_count': lease_count,
                    'own_count': own_count
                }
            else:
                count = len(self.buildings_df)
                result = {
                    'type': 'count',
                    'subtype': 'total',
                    'count': count
                }

        return result if result else None

    def _handle_time_based_queries(self, query: str) -> Optional[Dict]:
        """Handle queries about building age and construction dates"""
        result = {}
        
        if "oldest" in query:
            row = self.buildings_df.loc[self.buildings_df['Year Built'].idxmin()]
            result = {
                'type': 'age',
                'subtype': 'oldest',
                'data': row.to_dict(),
                'age': self.current_year - row['Year Built']
            }
        elif "newest" in query:
            row = self.buildings_df.loc[self.buildings_df['Year Built'].idxmax()]
            result = {
                'type': 'age',
                'subtype': 'newest',
                'data': row.to_dict(),
                'age': self.current_year - row['Year Built']
            }
        elif "built in" in query:
            year_match = re.search(r'\b20\d{2}\b', query)
            if year_match:
                year = int(year_match.group(0))
                buildings = self.buildings_df[self.buildings_df['Year Built'] == year]
                result = {
                    'type': 'built_in_year',
                    'year': year,
                    'count': len(buildings),
                    'buildings': buildings['Building ID'].tolist()
                }

        return result if result else None

    def _handle_location_queries(self, query: str) -> Optional[Dict]:
        """Handle queries about building locations"""
        result = {}
        
        if "region" in query or any(region in query for region in ["apac", "emea", "na"]):
            region_counts = self.buildings_df['Region'].value_counts().to_dict()
            result = {
                'type': 'location',
                'subtype': 'region_distribution',
                'data': region_counts
            }

        return result if result else None

    def _handle_comparison_queries(self, query: str) -> Optional[Dict]:
        """Handle queries comparing multiple buildings"""
        result = {}
        
        if "compare" in query:
            building_ids = re.findall(r'B\d{3}', query)
            if len(building_ids) >= 2:
                buildings_data = self.buildings_df[
                    self.buildings_df['Building ID'].isin(building_ids)
                ]
                result = {
                    'type': 'comparison',
                    'buildings': building_ids,
                    'data': buildings_data.to_dict('records')
                }

        return result if result else None

    def _validate_result(self, result: Dict) -> Dict:
        """Validate the result to ensure data consistency"""
        if not result:
            return {"error": "No data found"}
            
        # Add metadata about the source and timestamp
        result['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'data_source': 'verified_portfolio_data'
        }
        
        # Validate numerical values
        if 'data' in result and isinstance(result['data'], dict):
            for key, value in result['data'].items():
                if isinstance(value, (int, float)):
                    if value < 0:
                        result['warnings'] = result.get('warnings', []) + [
                            f"Negative value found for {key}"
                        ]
        
        return result