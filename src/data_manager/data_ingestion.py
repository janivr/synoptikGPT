import os
import pandas as pd
from sqlalchemy import create_engine

# Database connection string
DATABASE_URI = "postgresql+psycopg2://postgres:Janiv123@localhost:5433/real_estate"
engine = create_engine(DATABASE_URI)

# Function to load data into a specific table
def load_csv_to_table(file_path, table_name):
    try:
        # Read CSV file into DataFrame
        df = pd.read_csv(file_path)
        # Write DataFrame to PostgreSQL table
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Data loaded into table: {table_name}")
    except Exception as e:
        print(f"Error loading data into {table_name}: {e}")

# File paths for your CSV files
file_paths = {
    "buildings": "./data/Buildings.csv",
    "financials": "./data/Financial_Data.csv",
    "floor_occupancy": "./data/floors_occupancy.csv",
    "floor_utilization": "./data/floors_utilization_2024.csv",
    #"energy_consumption": "path_to_your_csv/energy_consumption.csv"
}

# Table names and corresponding file paths
for table_name, file_path in file_paths.items():
    load_csv_to_table(file_path, table_name)
    
for table_name, file_path in file_paths.items():
    if os.path.exists(file_path):
        print(f"{table_name} file exists: {file_path}")
    else:
        print(f"{table_name} file not found: {file_path}")
