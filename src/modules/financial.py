import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

class FinancialModule:
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize Financial Module with comprehensive data processing
        
        :param dataframe: DataFrame containing financial data
        """
        self._validate_dataframe(dataframe)
        self.data = dataframe
        self._preprocess_data()
    
    def _validate_dataframe(self, dataframe: pd.DataFrame):
        """
        Comprehensive data validation for financial DataFrame
        
        :param dataframe: DataFrame to validate
        :raises ValueError: If DataFrame is invalid
        """
        required_columns = [
            'Building ID', 'Date', 'Total Operating Expense (USD)',
            'Energy Costs (USD)', 'Utilities Costs (USD)', 'Maintenance Costs (USD)',
            'Catering Costs (USD)', 'Cleaning Costs (USD)', 'Security Costs (USD)',
            'Insurance Costs (USD)', 'Waste Disposal Costs (USD)', 'Other Costs (USD)'
        ]
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Validate date and numeric columns
        dataframe['Date'] = pd.to_datetime(dataframe['Date'])
        
        numeric_columns = [col for col in required_columns if col != 'Building ID' and col != 'Date']
        
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(dataframe[col]):
                raise ValueError(f"{col} must be numeric")
    
    def _preprocess_data(self):
        """
        Preprocess and enrich financial data
        """
        # Ensure date is datetime
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        
        # Add additional calculated columns
        self.data['Year'] = self.data['Date'].dt.year
        self.data['Month'] = self.data['Date'].dt.month
        
        # Calculate cost percentages
        total_expense_col = 'Total Operating Expense (USD)'
        cost_columns = [col for col in self.data.columns if col.endswith('Costs (USD)')]
        
        for col in cost_columns:
            self.data[f'{col} Percentage'] = \
                self.data[col] / self.data[total_expense_col] * 100
        
        # Validate total operating expense
        calculated_total = self.data[cost_columns].sum(axis=1)
        if not np.allclose(calculated_total, self.data[total_expense_col]):
            print("Warning: Calculated total expenses do not match the provided Total Operating Expense")
    
    def get_financial_overview(self) -> Dict[str, Any]:
        """
        Generate comprehensive financial portfolio overview
        
        :return: Dictionary of financial insights
        """
        cost_columns = [col for col in self.data.columns if col.endswith('Costs (USD)')]
        annual_summary = self.data.groupby('Year')[cost_columns + ['Total Operating Expense (USD)']].agg(['sum', 'mean'])
        
        return {
            'total_annual_expenses': dict(annual_summary['Total Operating Expense (USD)']['sum']),
            'avg_annual_expenses': dict(annual_summary['Total Operating Expense (USD)']['mean']),
            'expense_breakdown': {
                year: {col.replace(' Costs (USD)', ''): row[(col, 'sum')] 
                      for col in cost_columns}
                for year, row in annual_summary.iterrows()
            },
            'utilities_breakdown': self.get_utilities_breakdown(),
            'date_range': {
                'start': self.data['Date'].min(),
                'end': self.data['Date'].max()
            }
        }
    
    def get_utilities_breakdown(self, building_id: str = None, year: int = None) -> Dict[str, float]:
        """
        Get breakdown of utilities costs
        
        :param building_id: Optional building ID to filter data
        :param year: Optional year to filter data
        :return: Dictionary of utilities costs breakdown
        """
        query = self.data

        if building_id:
            query = query[query['Building ID'] == building_id]
        if year:
            query = query[query['Year'] == year]

        total_utilities = query['Utilities Costs (USD)'].sum()
        energy_costs = query['Energy Costs (USD)'].sum()
        other_utilities = total_utilities - energy_costs

        return {
            'Total Utilities Costs': total_utilities,
            'Energy Costs': energy_costs,
            'Other Utilities Costs': other_utilities
        }
    
    def analyze_building_financials(self, building_id: str) -> Optional[Dict[str, Any]]:
        """
        Perform detailed financial analysis for a specific building
        
        :param building_id: Unique identifier for the building
        :return: Comprehensive financial analysis or None
        """
        building_data = self.data[self.data['Building ID'] == building_id]
        
        if building_data.empty:
            return None
        
        cost_columns = [col for col in building_data.columns if col.endswith('Costs (USD)')]
        annual_summary = building_data.groupby('Year')[cost_columns + ['Total Operating Expense (USD)']].agg(['sum', 'mean'])
        
        # Cost trend analysis
        cost_trends = {}
        for col in cost_columns:
            yearly_costs = building_data.groupby('Year')[col].sum()
            if len(yearly_costs) > 1:
                # Calculate year-over-year change
                yoy_change = (yearly_costs.pct_change() * 100).dropna()
                cost_trends[col.replace(' Costs (USD)', '')] = {
                    'total_by_year': dict(yearly_costs),
                    'year_over_year_change': dict(yoy_change)
                }
        
        return {
            'building_id': building_id,
            'annual_expenses': dict(annual_summary['Total Operating Expense (USD)']['sum']),
            'avg_annual_expenses': dict(annual_summary['Total Operating Expense (USD)']['mean']),
            'cost_breakdown': {
                year: {col.replace(' Costs (USD)', ''): row[(col, 'sum')] 
                      for col in cost_columns}
                for year, row in annual_summary.iterrows()
            },
            'utilities_breakdown': self.get_utilities_breakdown(building_id),
            'cost_trends': cost_trends
        }
    
    def identify_cost_anomalies(self, building_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Identify cost anomalies and unusual spending patterns
        
        :param building_id: Optional specific building to analyze
        :return: List of cost anomalies
        """
        # Filter data if building_id is provided
        data = self.data[self.data['Building ID'] == building_id] if building_id else self.data
        
        anomalies = []
        
        cost_columns = [col for col in data.columns if col.endswith('Costs (USD)')]
        
        for column in cost_columns:
            # Calculate z-score for identifying outliers
            z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
            
            # Flag expenses more than 2.5 standard deviations from mean
            outliers = data[z_scores > 2.5]
            
            for _, row in outliers.iterrows():
                anomalies.append({
                    'building_id': row['Building ID'],
                    'date': row['Date'],
                    'cost_type': column.replace(' Costs (USD)', ''),
                    'amount': row[column],
                    'z_score': z_scores[row.name],
                    'description': f"Unusual {column.lower()} detected"
                })
        
        return anomalies
    
    def get_detailed_financial_summary(self):
        summary = {}
        for building_id in self.data['Building ID'].unique():
            building_data = self.data[self.data['Building ID'] == building_id]
            yearly_summary = building_data.groupby(building_data['Date'].dt.year).agg({
                'Energy Costs (USD)': 'sum',
                'Cleaning Costs (USD)': 'sum',
                'Utilities Costs (USD)': 'sum',
                'Maintenance Costs (USD)': 'sum',
                'Total Operating Expense (USD)': 'sum'
            }).to_dict()
            summary[building_id] = yearly_summary
        return summary
    
   
    def fetch_query_result(self, building_id: str, year: int, cost_type: str) -> str:
        """
        Fetch financial data for a specific building, year, and cost type.
        """
        if building_id not in self.data["Building ID"].values:
            return f"Building {building_id} is not found in the portfolio."
        
        # Filter data for the given building and year
        building_data = self.data[self.data["Building ID"] == building_id]
        try:
            value = building_data.loc[building_data["Year"] == year, cost_type].values[0]
            return f"The {cost_type} for Building {building_id} in {year} was ${value:,}."
        except IndexError:
            return f"No data available for {building_id} in {year}."
        except KeyError:
            return f"Invalid cost type '{cost_type}'. Please check the available categories."


