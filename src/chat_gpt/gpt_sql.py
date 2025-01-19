import os
import openai
import psycopg2
import logging
import json
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Logging Configuration
LOG_FILE = "app_log.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Console logging setup
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# Metadata Descriptions
buildings_metadata = {
    "table_name": "buildings",
    "columns": {
        "building_id": {"type": "string", "description": "Unique identifier for each building.", "primary_key": True},
        "city": {"type": "string", "description": "City where the building is located."},
        "address": {"type": "string", "description": "Full address of the building."},
        "country": {"type": "string", "description": "Country where the building is located."},
        "region": {"type": "string", "description": "Geographical region of the building (e.g., NA, APAC)."},
        "size": {"type": "integer", "description": "Total size of the building in square feet."},
        "floors": {"type": "integer", "description": "Number of floors in the building."},
        "purpose": {"type": "string", "description": "Primary purpose of the building (e.g., Office, Retail, Data Center)."},
        "ownership": {"type": "string", "description": "Ownership status of the building (e.g., Own, Lease)."},
        "year_built": {"type": "integer", "description": "The year the building was constructed."},
        "market_rate": {"type": "float", "description": "Market rate per square foot in USD."},
        "employee_capacity": {"type": "integer", "description": "Number of employees the building can accommodate."},
        "energy_target": {"type": "float", "description": "Energy consumption target per square foot per year."},
        "leed_certified": {"type": "boolean", "description": "Whether the building is LEED certified (Yes/No)."},
    },
    "relationships": {
        "foreign_keys": {
            "financials": "building_id",
            "floor_occupancy": "building_id",
            "floor_utilization": "building_id",
        }
    }
}

financials_metadata = {
    "table_name": "financials",
    "columns": {
        "building_id": {"type": "string", "description": "Reference to the Building ID in the buildings table.", "foreign_key": "buildings.building_id"},
        "date": {"type": "date", "description": "Date of the financial record."},
        "lease_cost": {"type": "float", "description": "Lease cost in USD for the specified period."},
        "total_operating_expense": {"type": "float", "description": "Total operating expenses in USD for the specified period."},
        "energy_costs": {"type": "float", "description": "Energy costs in USD for the specified period."},
        "utilities_costs": {"type": "float", "description": "Utilities costs in USD for the specified period."},
        "maintenance_costs": {"type": "float", "description": "Maintenance costs in USD for the specified period."},
        "catering_costs": {"type": "float", "description": "Catering costs in USD for the specified period."},
        "cleaning_costs": {"type": "float", "description": "Cleaning costs in USD for the specified period."},
        "security_costs": {"type": "float", "description": "Security costs in USD for the specified period."},
        "insurance_costs": {"type": "float", "description": "Insurance costs in USD for the specified period."},
        "waste_disposal_costs": {"type": "float", "description": "Waste disposal costs in USD for the specified period."},
        "other_costs": {"type": "float", "description": "Other miscellaneous costs in USD for the specified period."},
    },
    "relationships": {
        "foreign_keys": {"buildings": "building_id"}
    }
}


floor_occupancy_metadata = {
    "table_name": "floor_occupancy",
    "columns": {
        "building_id": {"type": "string", "description": "Unique identifier for each building.", "foreign_key": "buildings.building_id"},
        "floor": {"type": "integer", "description": "The floor number within the building."},
        "max_capacity": {"type": "integer", "description": "Maximum number of occupants the floor can accommodate."},
    },
    "relationships": {
        "foreign_keys": {"buildings": "building_id"}
    }
}

floor_utilization_metadata = {
    "table_name": "floor_utilization",
    "columns": {
        "building_id": {"type": "string", "description": "Unique identifier for each building.", "foreign_key": "buildings.building_id"},
        "floor": {"type": "integer", "description": "The floor number within the building."},
        "time": {"type": "datetime", "description": "Timestamp of the utilization record."},
        "occupancy": {"type": "integer", "description": "Number of occupants on the floor at the given time."},
    },
    "relationships": {
        "foreign_keys": {"buildings": "building_id"}
    }
}

metadata_info = {
    "buildings": buildings_metadata,
    "financials": financials_metadata,
    "floor_occupancy": floor_occupancy_metadata,
    "floor_utilization": floor_utilization_metadata,
}


# AI Agent Instructions
instructions = (
    "You are Sage, a data analysis assistant specializing in real estate datasets. Use the following metadata to understand the datasets:\n" +
    json.dumps(metadata_info, indent=4)  +
    "Provide concise and direct answers unless further clarification is requested." +
    "Format financial values with currency symbols and commas. " +
    "Avoid detailed explanations for straightforward questions. " +
    "Include relevant building details (location, size, purpose). " +
    "Explain any trends or patterns observed. " +
    "\nUse this information to answer questions about building attributes, financial data, occupancy, energy, maintenance, and trends. Provide accurate answers."
)

# OpenAI API Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key is missing from environment variables.")
client = OpenAI(api_key=openai.api_key)

def connect_to_db():
    try:
        database_uri = os.getenv("DATABASE_URI")

        if not database_uri:
            raise ValueError("DATABASE_URI environment variable is not set")
        
        if database_uri.startswith("postgresql+psycopg2://"):
            database_uri = database_uri.replace("postgresql+psycopg2://", "postgresql://")
        
        logging.info(f"Connecting to DB at host: localhost, port: 5433")

        # Establish connection
        return psycopg2.connect(database_uri)
    
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

# Generate SQL Query using GPT
def generate_sql_query(user_input, prev_context=None):
    try:
        
        # Default context values
        context = {
            "previous_question": None,
            "previous_field": None
        }
        
        # Update context if provided
        if prev_context:
            context.update(prev_context)                        
        
        prompt = f"""
        You are Synoptik Real Estate Assistant AI. 
        The database engine is PostgreSQL. Use PostgreSQL syntax for all SQL queries.
        Use the following conversation history and rules:
        Conversation History:
        {context}
        
        Conversation Context:
        Previous Question: "{context["previous_question"]}"
        
        Previous Field: "{context["previous_field"]}"
        Current Question: "{user_input}"
                
        Conversation Context Rules:
            1. Previous Question: "{context["previous_question"]}" used field: "{context["previous_field"]}"
            2. Current Question: "{user_input}"
            3. For follow-up questions using "and", use the same field/table as the previous question
    
        Use the following metadata to generate valid SQL queries:
        {metadata_info}

        For occupancy/utilization analysis:
        - occupancy is usually the number of people in a floor or building
        - utilization is usually the percentage of number of people versus (devided by) maximum capacity.
        - Use floor_utilization.occupancy for actual current usage
        - Use floor_occupancy.max_capacity for maximum allowed capacity
        - Group by building when aggregating floors
        - Join floor_utilization and floor_occupancy on both building_id AND floor        
        - Always include ALL floors from floor_occupancy, unless the question states differently
        - Include time period details from floor_utilization.time
        - Calculate average occupancy over specific time periods
        - Use LEFT JOIN to include all floors even if they have no utilization data
        - Order results logically (e.g., by floor number)
        
        For ranking queries:
        - Include relevant details (address, size, etc.)
        - Always show actual values, not just order
        - Order results appropriately (ASC/DESC)
        - Include all records that match criteria
        
        For highest/lowest queries:
        - When using MAX() or MIN() with other non-aggregated columns, include all non-aggregated columns in GROUP BY
        - Return full record details (building_id, address, etc.) for the max/min value
        - Use subqueries or window functions when appropriate to get the correct record

        Example structure for highest/lowest queries:
        SELECT b.building_id, b.address, b.employee_capacity
        FROM buildings b
        WHERE b.employee_capacity = (
            SELECT MAX(employee_capacity)
            FROM buildings
        )

        Rules:
        - Return ONLY the SQL query
        - NO explanations
        - NO markdown formatting
        - NO code blocks
        - Tables and columns are all lowercase
        
        Additional Rules:\n"
            1. Only use data that exists in the query results
            2. Never make up or infer numbers that aren't in the results
            3. Maintain consistency with previous questions in the conversation
            4. If the same field was used in a previous question (e.g., employee_capacity), use the same field for follow-up questions unless explicitly asked otherwise
            5. Always refer to prior questions and answers to maintain context.
            6. If the current question is ambiguous (e.g., "and the lowest"), infer the intent based on the most recent question.
            7. Always clarify your assumptions if needed.
        
        
        Query request: "{user_input}"
        Return ONLY the SQL query, no explanations.
        """
        print(f"Promt: {prompt}")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an SQL generator. Return ONLY SQL queries without any explanation."},                
                {"role": "system", "content": prompt}],
            max_tokens=200
        )
        
        sql_query = response.choices[0].message.content.strip()                
        
        logging.info(f"Generated SQL Query: {sql_query}")
        return sql_query
    except Exception as e:
        logging.error(f"Error generating SQL query: {e}")
        raise

# Execute SQL Query
def execute_query(sql_query):
    conn = None
    try:
        conn = connect_to_db()
        if conn is None:
            return {"error": "Database connection failed", "rows": [], "columns": []}
            
        cursor = conn.cursor()
        logging.info(f"Executing SQL Query: {sql_query}")
        cursor.execute(sql_query)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            logging.info(f"Query Results - Columns: {columns}")
            logging.info(f"Query Results - Rows: {rows}")
            return {"columns": columns, "rows": rows}
        else:
            conn.commit()
            return {"message": "Query executed successfully.", "rows": [], "columns": []}
    except Exception as e:
        logging.error(f"Query execution failed: {e}")
        return {"error": str(e), "rows": [], "columns": []}
    finally:
        if conn:
            conn.close()
            
def analyze_data_with_gpt(user_query, columns, rows, prev_context=None):
    """
    Use GPT to analyze SQL query results and generate a natural language response.

    Args:
        user_query (str): The original question from the user.
        columns (list): List of column names from the SQL query result.
        rows (list): List of rows (data) from the SQL query result.

    Returns:
        str: A natural language response generated by GPT.
    """
    try:
        
        # Default context values
        context = {
            "previous_question": None,
            "previous_field": None
        }
        
        # Update context if provided
        if prev_context:
            context.update(prev_context)
        
        previous_field = prev_context["previous_field"] if prev_context else None
        
        # Prepare the prompt for GPT
        data_summary = f"Query results:\nColumns: {columns}\nRows:\n" + "\n".join(str(row) for row in rows[:10])  # Limit to first 10 rows
        
        prompt = (
            f"You are an AI assistant specializing in real estate analysis.\n"
            "Format your response following these rules:\n"
            "1. For currency values:\n"
            "   - Always include $ symbol\n"
            "   - Use commas for thousands\n"
            "   - Show cents for precision (.00)\n"
            "2. For rankings or comparisons:\n"
            "   - Use numbered list format\n"
            "   - Include building ID and address in parentheses\n"
            "   - Show relevant metrics with proper units (sqft, USD, etc.)\n"
            "   - Indent details with bullet points\n"
            "3. For occupancy/utilization:\n"
            "   - Occupancy should be shown as number of people (e.g., '45 people')\n"
            "   - Utilization should be shown as percentage (e.g., '45.2%')\n"
            "   - Always specify the time period being analyzed\n"
            "       -- 3.1. Time periods must be explicitly stated:"
            "           --- Specify if showing current occupancy\n"
            "           --- Specify if showing averages (daily, weekly, monthly, yearly)\n"
            "           --- Include the exact date range being analyzed\n"
            "       -- 3.2. Missing data:\n"
            "           --- List ALL floors from floor_occupancy\n"
            "           --- Explicitly note any floors without utilization data\n"
            "           --- Explain any gaps in the data\n"
            "       -- 3.3. Metrics must be clear:\n"
            "           --- Occupancy = actual number of people\n"
            "           --- Utilization = percentage of maximum capacity\n"
            "           --- Always include both metrics for completeness\n"
            "4. For trends and patterns:\n"
            "   - Explicitly answer any questions about patterns or trends\n"
            "   - Identify notable variations or anomalies\n"
            "   - Compare against relevant benchmarks\n"
            "5. Time periods:\n"
            "   - Always specify the time frame for any analysis\n"
            "   - Use clear date ranges (e.g., 'During 2023', 'From March to April 2023')\n"            
            "6. If values are identical, explicitly mention this\n"
            "7. For large numbers:\n"
            "   - Be specific with units (USD, sqft, etc.)\n"
            "   - Use commas for readability (e.g., 1,000,000)\n"
            "   - Round decimal numbers to 2 places\n"
            "8. Context Rules:\n"
            f"   - Previous answer used field: {previous_field}\n"
            f"   - Previous field used: {previous_field if previous_field else 'None'}\n"
            "   - For follow-up questions using 'and', maintain EXACT same analysis as previous question\n"
            "   - NEVER switch metrics between questions unless explicitly requested\n"
            "   - If user asks 'and the lowest?', use the SAME metric as 'highest'\n"
            "Additional Rules:\n"
                "1. Only use data that exists in the query results\n"
                "2. Never make up or infer numbers that aren't in the results\n"
                "3. Maintain consistency with previous questions in the conversation\n"
                "4. If the same field was used in a previous question (e.g., employee_capacity), "
                "5. use the same field for follow-up questions unless explicitly asked otherwise\n"
                "6. Always maintain context from previous question\n"
                "7. If previous question was about time patterns, maintain time analysis\n"
                "8. For 'and in [building]' questions, use same analysis as previous question\n"
                "9. Format occupancy consistently:\n"
                "   • Building details on first line\n"
                "   • Time-based metrics on subsequent lines with consistent indentation\n"
                "   • Show occupancy as whole numbers with 'people' unit\n"
                "   • Sort by time for time-based analysis\n"
            f"Question: {user_query}\n"
            f"{data_summary}\n"            
            f"Provide a well-formatted response following the above rules.\n"
            "Provide comprehensive answers that address all parts of the question.\n"
            ". No explanations or interpretations.\n"
        )

        # Use OpenAI's API to generate the response
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are Sage, a data analyst. Provide only direct, factual answers without explanation."}, 
                      {"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error analyzing data with GPT: {e}")
        raise

def fetch_db_schema(connection):
    try:
        cursor = connection.cursor()
        query = """
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public';
        """
        cursor.execute(query)
        schema = cursor.fetchall()
        cursor.close()
        return schema
    except Exception as e:
        logging.error(f"Error fetching database schema: {e}")
        return []

import re

import re

def validate_query(sql_query):
    """
    Validates the SQL query against the metadata to ensure it uses valid tables and columns.
    """
    errors = []
    sql_query = sql_query.lower()  # Normalize for case-insensitivity

    for table, table_metadata in metadata_info.items():
        if table.lower() in sql_query:  # Check if the table is used in the query
            # Check if any valid column from this table is used in the query
            valid_columns_used = any(re.search(rf'\b{col.lower()}\b', sql_query) for col in table_metadata["columns"])
            if not valid_columns_used:
                errors.append(f"No valid columns from table '{table}' are used in the query.")

    # Return errors if found, otherwise return True
    return errors if errors else False

def execute_validated_query(query, connection=None):
    """
    Validate the query and execute it if valid.

    Args:
        query (str): The SQL query to validate and execute.
        connection: The database connection object.

    Returns:
        dict: Query results or validation error details.
    """
    errors = validate_query(query)
    if errors:
        logging.error(f"Query validation failed: {errors}")
        return {"error": "Query validation failed", "details": errors}

    # If valid, execute the query
    try:
        return execute_query(query)
    except Exception as e:
        logging.error(f"Query execution failed: {e}")
        return {"error": "Query execution failed", "details": str(e)}


def calculate_success_rate(log_file="query_analytics.log"):
    try:
        with open(log_file, "r") as f:
            logs = f.readlines()
        total_queries = len(logs)
        successful_queries = sum(1 for log in logs if "Success" in log)
        return (successful_queries / total_queries) * 100 if total_queries else 0
    except FileNotFoundError:
        return 0


def log_query_analytics(query, outcome, log_file="query_analytics.log"):
    with open(log_file, "a") as f:
        f.write(f"{datetime.now()} | Query: {query} | Outcome: {outcome}\n")



# Main Function
def main():
    print("Welcome to GPT-SQL!")
    logging.info("GPT-SQL Assistant started.")
    while True:
        user_input = input("Enter your query (or type 'exit' to quit): ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            logging.info("GPT-SQL Assistant exited.")
            break
        try:
            sql_query = generate_sql_query(user_input)
            result = execute_validated_query(sql_query)
            print("Query Results:")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
