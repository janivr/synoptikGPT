# src/utils/data_loader.py
import pandas as pd
import streamlit as st
import os
import logging

class DataLoader:
    @staticmethod
    @st.cache_data
    def load_buildings_data(filepath=None):
        """
        Load buildings data
        
        :param filepath: Optional custom filepath, defaults to project data directory
        :return: DataFrame with buildings data
        """
        if filepath is None:
            filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'Buildings.csv')
        
        logging.info(f"Attempting to load buildings data from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logging.info(f"Successfully loaded buildings data. Shape: {df.shape}")
            logging.info(f"Columns: {df.columns.tolist()}")
            return df
        except FileNotFoundError:
            logging.warning(f"Buildings data file not found at {filepath}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading buildings data: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data
    def load_financial_data(filepath=None):
        """
        Load financial data
        
        :param filepath: Optional custom filepath, defaults to project data directory
        :return: DataFrame with financial data
        """
        if filepath is None:
            filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'Financial_Data.csv')
        
        logging.info(f"Attempting to load financial data from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            logging.info(f"Successfully loaded financial data. Shape: {df.shape}")
            logging.info(f"Columns: {df.columns.tolist()}")
            return df
        except FileNotFoundError:
            logging.warning(f"Financial data file not found at {filepath}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading financial data: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def validate_data(buildings_df, financial_df):
        """
        Validate the loaded data
        
        :param buildings_df: DataFrame with buildings data
        :param financial_df: DataFrame with financial data
        :return: Boolean indicating if data is valid
        """
        if buildings_df.empty or financial_df.empty:
            logging.error("One or both datasets are empty")
            return False

        required_buildings_columns = ['Building ID', 'Location', 'Size', 'Year Built', 'LEED Certified']
        required_financial_columns = ['Building ID', 'Date', 'Total Operating Expense (USD)']


        missing_buildings_columns = [col for col in required_buildings_columns if col not in buildings_df.columns]
        missing_financial_columns = [col for col in required_financial_columns if col not in financial_df.columns]

        if missing_buildings_columns:
            logging.error(f"Missing required columns in buildings data: {missing_buildings_columns}")
            return False

        if missing_financial_columns:
            logging.error(f"Missing required columns in financial data: {missing_financial_columns}")
            return False

        logging.info("Data validation passed successfully")
        return True