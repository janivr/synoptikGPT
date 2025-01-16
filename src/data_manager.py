from typing import Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime

class DataManager:
    def __init__(self):
        self.data_sources = {}
        self.relationships = {}
        self.metadata = {}
        
    async def register_data_source(
        self,
        name: str,
        path: str,
        data_type: str,
        metadata: Dict = None
    ) -> bool:
        """Register a new data source"""
        try:
            # Load data based on type
            if data_type == 'csv':
                data = pd.read_csv(path)
            elif data_type == 'excel':
                data = pd.read_excel(path)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
            # Store data and metadata
            self.data_sources[name] = data
            self.metadata[name] = {
                'columns': list(data.columns),
                'types': data.dtypes.to_dict(),
                'last_updated': datetime.now().isoformat(),
                'row_count': len(data),
                'user_metadata': metadata or {}
            }
            
            # Discover relationships
            self._discover_relationships(name)
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to register data source {name}: {str(e)}")

    def get_schema(self) -> Dict:
        """Get the current schema of all data sources"""
        return {
            'data_sources': {
                name: self.metadata[name]
                for name in self.data_sources
            },
            'relationships': self.relationships,
            'available_metrics': self._get_available_metrics()
        }

    def _discover_relationships(self, new_source: str):
        """Discover relationships between data sources"""
        for existing_source in self.data_sources:
            if existing_source != new_source:
                common_cols = set(self.data_sources[new_source].columns) & \
                            set(self.data_sources[existing_source].columns)
                            
                if common_cols:
                    self.relationships[f"{new_source}_{existing_source}"] = {
                        'type': 'common_columns',
                        'columns': list(common_cols)
                    }

    def _get_available_metrics(self) -> Dict:
        """Get available metrics for each data source"""
        metrics = {}
        for name, df in self.data_sources.items():
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            date_cols = df.select_dtypes(include=['datetime64']).columns
            
            metrics[name] = {
                'numeric': list(numeric_cols),
                'temporal': list(date_cols),
                'categorical': list(set(df.columns) - set(numeric_cols) - set(date_cols))
            }
            
        return metrics

    async def execute_query(self, query_plan: Dict) -> pd.DataFrame:
        """Execute a query plan across data sources"""
        # Implementation details for query execution
        pass

    def validate_query_plan(self, plan: Dict) -> bool:
        """Validate a query plan against available data"""
        # Implementation details for validation
        pass