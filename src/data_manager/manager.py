from typing import Dict, Any, Optional
import pandas as pd
import logging
from datetime import datetime
from src.utils.utils import convert_numpy_types

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self):
        self.data_sources = {}
        self.relationships = {}
        self.metadata = {}

    def register_data_source(self, name: str, data: pd.DataFrame, metadata: Dict = None) -> bool:
        """Register a new data source"""
        try:
            # Store data and metadata
            self.data_sources[name] = data
            
            # Convert dtypes to serializable format
            dtype_dict = {col: str(dtype) for col, dtype in data.dtypes.items()}
            
            self.metadata[name] = {
                'columns': list(data.columns),
                'types': dtype_dict,
                'last_updated': datetime.now().isoformat(),
                'row_count': len(data),
                'user_metadata': metadata or {}
            }
            
            # Discover relationships
            self._discover_relationships(name)
            
            logger.info(f"Successfully registered data source: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register data source {name}: {str(e)}")
            raise

    def get_schema(self) -> Dict:
        """Get the current schema of all data sources"""
        schema_data = {
            'data_sources': {
                name: self.metadata[name]
                for name in self.data_sources
            },
            'relationships': self.relationships,
            'available_metrics': self._get_available_metrics()
        }
        return convert_numpy_types(schema_data)

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

    def query_data(self, query_plan: Dict) -> Dict:
        """Execute a query on the data sources"""
        try:
            source = query_plan.get('source')
            if not source or source not in self.data_sources:
                raise ValueError(f"Invalid data source: {source}")
                
            df = self.data_sources[source]
            
            # Apply filters if any
            if 'filters' in query_plan:
                for filter_col, filter_val in query_plan['filters'].items():
                    if isinstance(filter_val, list):
                        df = df[df[filter_col].isin(filter_val)]
                    else:
                        df = df[df[filter_col] == filter_val]
            
            # Apply grouping if specified
            if 'group_by' in query_plan:
                group_cols = query_plan['group_by']
                agg_cols = query_plan.get('aggregate', {})
                
                result = df.groupby(group_cols).agg(agg_cols).reset_index()
            else:
                result = df
            
            # Serialize the result
            return {
                'data': convert_numpy_types(result),
                'row_count': len(result)
            }
            
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise