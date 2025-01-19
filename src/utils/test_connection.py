from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Replace with your DATABASE_URI
DATABASE_URI = "postgresql+psycopg2://postgres:Janiv123@localhost:5433/real_estate"


def test_connection(uri):
    try:
        # Create a database engine
        engine = create_engine(uri)
        # Connect to the database
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))  
            print("Connection successful!")
            for row in result:
                print(f"PostgreSQL Version: {row[0]}")
    except Exception as e:
        print(f"Failed to connect: {e}")

# Test the connection
test_connection(DATABASE_URI)
