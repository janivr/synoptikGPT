from typing import Any
import numpy as np
import pandas as pd
import json

def convert_numpy_types(obj: Any) -> Any:
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, bool):
        return bool(obj)
    # Add pandas types
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (pd.Int64Dtype, pd.StringDtype, pd.BooleanDtype)):
        return str(obj)
    return obj

class JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        return convert_numpy_types(obj)