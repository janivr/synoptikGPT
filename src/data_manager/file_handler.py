from typing import Dict, Any, BinaryIO
import pandas as pd
import json
from io import StringIO
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    @staticmethod
    async def process_upload(
        file: BinaryIO,
        filename: str,
        file_type: str
    ) -> Dict[str, Any]:
        """Process an uploaded file and return its data and metadata"""
        try:
            # Read file based on type
            if file_type == 'csv':
                data = pd.read_csv(StringIO(file.read().decode('utf-8')))
            elif file_type == 'excel':
                data = pd.read_excel(file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Generate metadata
            metadata = {
                'filename': filename,
                'columns': list(data.columns),
                'row_count': len(data),
                'column_types': {col: str(dtype) for col, dtype in data.dtypes.items()},
                'numeric_columns': list(data.select_dtypes(include=['int64', 'float64']).columns),
                'categorical_columns': list(data.select_dtypes(include=['object']).columns),
                'sample_data': data.head(5).to_dict('records')
            }

            return {
                'data': data,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            raise

    @staticmethod
    def validate_file(data: pd.DataFrame, expected_schema: Dict) -> Dict[str, Any]:
        """Validate uploaded file against expected schema"""
        validation_results = {
            'is_valid': True,
            'issues': []
        }

        # Check required columns
        missing_columns = set(expected_schema['required_columns']) - set(data.columns)
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['issues'].append(f"Missing required columns: {missing_columns}")

        # Check data types
        for col, expected_type in expected_schema['column_types'].items():
            if col in data.columns:
                actual_type = data[col].dtype
                if not pd.api.types.is_dtype_equal(actual_type, expected_type):
                    validation_results['is_valid'] = False
                    validation_results['issues'].append(
                        f"Column {col} has type {actual_type}, expected {expected_type}"
                    )

        return validation_results