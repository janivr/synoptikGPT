from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self):
        self.operations = {
            'filter': self._filter_data,
            'aggregate': self._aggregate_data,
            'join': self._join_data,
            'sort': self._sort_data,
            'calculate': self._calculate_metrics
        }

    async def execute_query(self, query_plan: Dict, data_manager: Any) -> Dict[str, Any]:
        """Execute a query plan and return results"""
        try:
            # Track data lineage
            lineage = []
            
            # Get required data sources
            data = {}
            for source in query_plan['data_sources']:
                data[source] = data_manager.data_sources[source].copy()
                lineage.append({
                    'source': source,
                    'operation': 'load',
                    'timestamp': datetime.now().isoformat()
                })

            # Execute operations in sequence
            result = None
            for operation in query_plan['operations']:
                op_type = operation['type']
                if op_type in self.operations:
                    result = await self.operations[op_type](
                        data=data,
                        params=operation['params'],
                        current_result=result
                    )
                    lineage.append({
                        'operation': op_type,
                        'params': operation['params'],
                        'timestamp': datetime.now().isoformat()
                    })

            return {
                'result': result,
                'lineage': lineage,
                'metadata': {
                    'execution_time': datetime.now().isoformat(),
                    'row_count': len(result) if isinstance(result, pd.DataFrame) else 1
                }
            }

        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise

    async def _filter_data(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict,
        current_result: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Apply filters to dataframe"""
        df = current_result if current_result is not None else data[params['source']]
        
        for condition in params['conditions']:
            column = condition['column']
            operator = condition['operator']
            value = condition['value']

            if operator == 'equals':
                df = df[df[column] == value]
            elif operator == 'greater_than':
                df = df[df[column] > value]
            elif operator == 'less_than':
                df = df[df[column] < value]
            elif operator == 'in':
                df = df[df[column].isin(value)]
            elif operator == 'contains':
                df = df[df[column].str.contains(value, case=False)]

        return df

    async def _aggregate_data(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict,
        current_result: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Perform aggregation operations"""
        df = current_result if current_result is not None else data[params['source']]
        
        # Group by columns if specified
        if 'group_by' in params:
            grouped = df.groupby(params['group_by'])
        else:
            grouped = df

        # Apply aggregation functions
        agg_funcs = {}
        for metric in params['metrics']:
            col = metric['column']
            func = metric['function']
            if func == 'sum':
                agg_funcs[col] = 'sum'
            elif func == 'average':
                agg_funcs[col] = 'mean'
            elif func == 'count':
                agg_funcs[col] = 'count'
            elif func == 'min':
                agg_funcs[col] = 'min'
            elif func == 'max':
                agg_funcs[col] = 'max'

        return grouped.agg(agg_funcs).reset_index()

    async def _join_data(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict,
        current_result: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Join dataframes"""
        left_df = current_result if current_result is not None else data[params['left']]
        right_df = data[params['right']]

        return pd.merge(
            left_df,
            right_df,
            how=params.get('how', 'inner'),
            on=params['on']
        )

    async def _sort_data(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict,
        current_result: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Sort dataframe"""
        df = current_result if current_result is not None else data[params['source']]
        
        return df.sort_values(
            by=params['columns'],
            ascending=params.get('ascending', True)
        )

    async def _calculate_metrics(
        self,
        data: Dict[str, pd.DataFrame],
        params: Dict,
        current_result: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Calculate custom metrics"""
        df = current_result if current_result is not None else data[params['source']]
        
        for metric in params['metrics']:
            if metric['type'] == 'ratio':
                df[metric['name']] = df[metric['numerator']] / df[metric['denominator']]
            elif metric['type'] == 'difference':
                df[metric['name']] = df[metric['minuend']] - df[metric['subtrahend']]
            elif metric['type'] == 'percentage':
                df[metric['name']] = (df[metric['part']] / df[metric['whole']]) * 100

        return df