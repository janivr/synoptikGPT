import pandas as pd

class DataLoader:
    @staticmethod
    def load_buildings_data(file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)

    @staticmethod
    def load_financial_data(file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)