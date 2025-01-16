import os
import re
from openai import OpenAI
from typing import List, Dict, Any, Optional, Union
import numpy as np
import json
import pandas as pd
from datetime import datetime
from ..modules.query_processor import QueryProcessor
from ..utils.response_generator import ResponseGenerator
import openai

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)
    
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
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj

def create_system_prompt(buildings_module, financial_module):
    
     # Access the dataframes from the modules
    buildings_df = buildings_module.data
    financial_df = financial_module.data
    
    # Metadata descriptions for buildings and financial data
    buildings_metadata = {
        "Building ID": "Unique identifier for each building.",
        "City": "City where the building is located.",
        "Address": "Full address of the building.",
        "Country": "Country where the building is located.",
        "Region": "Geographical region of the building (e.g., NA, APAC).",
        "Size": "Total size of the building in square feet.",
        "Floors": "Number of floors in the building.",
        "Purpose": "Primary purpose of the building (e.g., Office, Retail, Data Center).",
        "Ownership": "Ownership status of the building (e.g., Own, Lease).",
        "Year Built": "The year the building was constructed.",
        "Market Rate ($/sqft)": "Market rate per square foot in USD.",
        "Employee Capacity": "Number of employees the building can accommodate.",
        "Energy Target (kWh/sqft/yr)": "Energy consumption target per square foot per year.",
        "LEED Certified": "Whether the building is LEED certified (Yes/No).",
        "Total Operating Expense (2024)": "Total operating expense in USD for the year 2024."
    }

    financial_metadata = {
        "Record Id": "Unique identifier for each financial record.",
        "Building ID": "Reference to the Building ID in the buildings dataset.",
        "Date": "Date of the financial record.",
        "Lease Cost (USD)": "Lease cost in USD for the specified period.",
        "Total Operating Expense (USD)": "Total operating expenses in USD for the specified period.",
        "Energy Costs (USD)": "Energy costs in USD for the specified period.",
        "Utilities Costs (USD)": "Utilities costs in USD for the specified period.",
        "Maintenance Costs (USD)": "Maintenance costs in USD for the specified period.",
        "Catering Costs (USD)": "Catering costs in USD for the specified period.",
        "Cleaning Costs (USD)": "Cleaning costs in USD for the specified period.",
        "Security Costs (USD)": "Security costs in USD for the specified period.",
        "Insurance Costs (USD)": "Insurance costs in USD for the specified period.",
        "Waste Disposal Costs (USD)": "Waste disposal costs in USD for the specified period.",
        "Other Costs (USD)": "Other miscellaneous costs in USD for the specified period."
    }

 
    # Example questions for GPT
    example_questions = [
        "Which building is the most expensive one?",
        "Which building has the highest capacity?",
        "Which building has the lowest capacity?",
        "Where is the highest energy target?",
        "How many buildings are LEED certified?",
        "How many buildings are in APAC, EMEA, and NA?",
        "What is the oldest building?",
        "What is the newest building?",
        "How many buildings are in lease vs. owned?",
        "What was the total energy cost of B002 in 2023?",
        "What were the cleaning costs for building B004 in March 2023?",
        "Compare the energy costs of B002 between January 2023 and February 2023.",
        "How did B001's cleaning costs change from March 2023 to April 2023?",
        "Compare the total operating expenses of B001 and B002 for 2023.",
        "Which building had the highest energy costs in January 2023?",
        "How did B001's energy costs trend throughout 2023?",
        "Show me the monthly utility costs for B002 in 2023.",
        "For our New York buildings, what were their total energy costs in March 2023?",
        "Which LEED-certified building had the highest cleaning costs in 2023?",
        "How many buildings were built in 2022?",
        "What building was built in 2018?",
        "How many buildings are less than 3 years old?",
        "How many buildings are more than 15 years old?",
        "In which year did we build the most buildings?",
        "When was the building in New York built?",
        "What is the average energy cost per building for 2023?",
        "What is the total operating expense for all buildings in 2024?",
        "Which building in EMEA had the highest lease costs in 2022?"
    ]

    # Calculate dataset-wide statistics
    total_buildings = buildings_df["Building ID"].nunique()
    total_records = len(buildings_df)
    financial_records = len(financial_df)

    # Add structured query examples
    query_examples = {
        "Most expensive building": {
            "user_query": "Which building is the most expensive one?",
            "query_plan": {
                "data_needed": ["Building ID", "Location", "Total Operating Expense (2024)"],
                "calculations": [{
                    "type": "max",
                    "field": "Total Operating Expense (2024)",
                    "dataset": "buildings"
                }],
                "filters": [],
                "time_period": {"year": 2024}
            }
        },
        "Building capacity": {
            "user_query": "Which building has the highest capacity?",
            "query_plan": {
                "data_needed": ["Building ID", "Location", "Employee Capacity"],
                "calculations": [{
                    "type": "max",
                    "field": "Employee Capacity",
                    "dataset": "buildings"
                }],
                "filters": [],
                "time_period": None
            }
        },
        "Energy costs trend": {
            "user_query": "How did B001's energy costs trend throughout 2023?",
            "query_plan": {
                "data_needed": ["Building ID", "Date", "Energy Costs (USD)"],
                "calculations": [{
                    "type": "trend",
                    "field": "Energy Costs (USD)",
                    "building_id": "B001",
                    "dataset": "financial"
                }],
                "filters": [
                    {"dataset": "financial", "field": "Building ID", "operator": "equals", "value": "B001"}
                ],
                "time_period": {"year": 2023}
            }
        },
        "LEED certified count": {
            "user_query": "How many buildings are LEED certified?",
            "query_plan": {
                "data_needed": ["Building ID", "LEED Certified"],
                "calculations": [{
                    "type": "count",
                    "field": "Building ID",
                    "dataset": "buildings"
                }],
                "filters": [
                    {"dataset": "buildings", "field": "LEED Certified", "operator": "equals", "value": "checked"}
                ],
                "time_period": None
            }
        }
    }


    # Create the system prompt
    system_prompt = f"""
You are Sage, a highly intelligent AI assistant specializing in real estate portfolio management. Your job is to analyze and answer user queries about buildings and their financial data using the two datasets described below.

### 1. Buildings Dataset
Metadata:
{json.dumps(buildings_metadata, indent=2, cls=CustomJSONEncoder)}


### 2. Financial Dataset
Metadata:
{json.dumps(financial_metadata, indent=2, cls=CustomJSONEncoder)}

### Examples of Valid Questions:
{json.dumps(example_questions, indent=2)}

Query Processing Instructions:
1. Analyze the user's question to determine required data and calculations
2. Create a structured query plan with these components:
   - data_needed: List of required fields
   - calculations: List of required calculations (type, field, dataset)
   - filters: Any conditions to apply
   - time_period: Time constraints if applicable
   - grouping: Grouping requirements if needed

Example Query Plans:
{json.dumps(query_examples, indent=2, cls=CustomJSONEncoder)}

Available Calculation Types:
- max: Find maximum value with context
- min: Find minimum value with context
- sum: Calculate total with optional grouping
- average: Calculate average with optional grouping
- count: Count records with optional grouping
- trend: Analyze changes over time

Response Guidelines:
1. Always include specific numbers and metrics
2. Format financial values with currency symbols and commas
3. Provide context for the answers
4. Include relevant building details (location, size, purpose)
5. Explain any trends or patterns observed

Available Data:
    - Total Buildings: {total_buildings}
    - Total Building Records: {total_records}
    - Total Financial Records: {financial_records}
    - Columns in Building Dataset: {list(buildings_df.columns)}
    - Columns in Financial Dataset: {list(financial_df.columns)}
    - Date Range: {financial_df['Date'].min()} to {financial_df['Date'].max()}

    
 **Key Guidelines**:
    1. Interpret user queries and dynamically apply filters to the dataset.
    2. Use the available data to calculate and compare metrics like totals, averages, or counts.
    3. Provide clear explanations when data is unavailable or cannot be calculated.
    4. Always format financial values (e.g., "$10,000").
    
You have access to two datasets:

1. **Buildings Dataset**:
- Columns: Building ID, Location, Address, Country, Region, Size, Floors, Purpose, Ownership, Year Built, Market Rate ($/sqft), Employee Capacity, Energy Target (kWh/sqft/yr), LEED Certified, Financial Data, Total Operating Expense (2024).
- Example Row: {{Building ID: B001, Location: New York, Year Built: 2000, Total Operating Expense (2024): 450,000}}

2. **Financial Dataset**:
- Columns: Record ID, Building ID, Date, Lease Cost (USD), Total Operating Expense (USD), Energy Costs (USD), Utilities Costs (USD), Maintenance Costs (USD), Catering Costs (USD), Cleaning Costs (USD), Security Costs (USD), Insurance Costs (USD), Waste Disposal Costs (USD), Other Costs (USD).
- Example Row: {{Building ID: B001, Date: 2023-01-01, Cleaning Costs (USD): 500}}

### How to Query the Data:
- **Aggregates**: You can ask for sums, averages, minimums, maximums, or counts for any column.
- **Filters**: You can specify conditions like "buildings in New York" or "expenses in 2023."
- **Comparisons**: Compare values, such as "Which building has higher energy costs?"
- **Trends**: Analyze changes over time, e.g., "How did cleaning costs trend in 2023?"

If a query cannot be answered because of missing data, explain why.    
### Instructions for Handling User Queries:
1. **Understand the Query**: Analyze the user's question and determine its intent (e.g., identifying a specific building, comparing costs, grouping, filtering, or aggregating data).
2. **Data Access and Operations**:
   - Use the Buildings Dataset for questions related to building properties (e.g., location, size, year built, LEED certification).
   - Use the Financial Dataset for cost-related queries (e.g., energy, cleaning, operating expenses).
   - Combine both datasets for questions that span both (e.g., "For LEED-certified buildings, what were the total energy costs in 2023?").
3. **Dynamic Query Processing**:
   - Perform operations like filtering (e.g., buildings in NA), grouping (e.g., total costs by year), sorting (e.g., oldest building), or aggregation (e.g., total costs across all buildings).
   - Use date ranges or specific time frames when provided (e.g., "January 2023" or "Q1 2022").
4. **Unavailable Data**:
   - If data is missing or unavailable, explain this clearly to the user and suggest alternatives (e.g., "No data available for Cleaning Costs in March 2023").
5. **Formatting**:
   - Provide numerical outputs in readable formats (e.g., $100,000 for currency, commas for large numbers).
   - Include building IDs and names when listing results to improve clarity.
6. **Clarify Ambiguities**:
   - If the query is unclear or ambiguous, ask for clarification.

Your role is to provide detailed, accurate, and well-formatted answers based on the datasets provided. Always prioritize accuracy and explain any assumptions made in the analysis.
"""
    return system_prompt



def summarize_portfolio_stats(stats):
    # Implement a summarization logic here
    return {k: stats[k] for k in ['total_buildings', 'total_portfolio_size', 'avg_building_size']}

def summarize_buildings(buildings_data):
    # Implement a summarization logic here
    return {
        'total_buildings': len(buildings_data),
        'locations': list(buildings_data['Location'].unique()),
        'size_range': f"{buildings_data['Size'].min()} - {buildings_data['Size'].max()}"
    }

def summarize_financials(financial_data):
    # print("Financial data structure:")
    # print(json.dumps(financial_data, indent=2, default=str))
    
    summary = {}
    for building_id, yearly_data in financial_data.items():
        summary[building_id] = {
            'years_available': list(yearly_data.keys())
        }
        
        # Safely calculate totals
        total_energy_cost = 0
        total_operating_expense = 0
        for year, data in yearly_data.items():
            total_energy_cost += data.get('Energy Costs (USD)', {}).get('sum', 0)
            total_operating_expense += data.get('Total Operating Expense (USD)', {}).get('sum', 0)
        
        summary[building_id]['total_energy_cost'] = total_energy_cost
        summary[building_id]['total_operating_expense'] = total_operating_expense
    
    return summary



def ask_gpt(messages: List[Dict], buildings_module, financial_module):
    """
    Enhanced GPT query system with data processing capabilities.
    """
    try:
        if not messages or not isinstance(messages, list) or not messages[-1].get("content"):
            return "Error: Invalid query format"
            
        # Get user's question
        user_message = messages[-1]["content"]
        
        if not buildings_module or not financial_module:
            return "Error: Data modules not properly initialized"
            
        # Process the query using QueryProcessor
        processor = QueryProcessor(buildings_module, financial_module)
        query_result = processor.process_query(user_message)
        
        # Handle error results
        if 'error' in query_result:
            error_msg = query_result['error']
            response_messages = [
                {"role": "system", "content": "You are a helpful real estate portfolio analyst."},
                {"role": "user", "content": f"Please rephrase this error message in a polite way: {error_msg}"}
            ]
            
            error_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=response_messages,
                temperature=0.3
            )
            
            return error_response.choices[0].message.content.strip()
        
        # Generate initial response using ResponseGenerator
        response_gen = ResponseGenerator()
        data_response = response_gen.generate_response(query_result)
        
        # Use GPT to enhance the response while maintaining accuracy
        enhancement_prompt = f"""
Based on this factual response from our real estate portfolio analysis:
"{data_response}"

Please enhance this response to make it more natural while:
1. Maintaining all numerical values exactly as provided
2. Not adding any information not present in the original
3. Not using generic phrases like "feel free to ask"
4. Keeping the same factual content
"""

        enhancement_messages = [
            {"role": "system", "content": "You are a real estate portfolio analyst. Keep responses factual and precise."},
            {"role": "user", "content": enhancement_prompt}
        ]
        
        enhanced_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=enhancement_messages,
            temperature=0.3  # Keep it conservative to maintain accuracy
        )
        
        return enhanced_response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"An error occurred: {str(e)}"

# [Keep your existing helper functions]

    

def execute_query_plan(query_plan: Dict, buildings_module, financial_module) -> Dict:
    """
    Execute the query plan and return results.
    """
    results = {}
    buildings_df = buildings_module.data
    financial_df = financial_module.data
    
    # Apply filters
    if query_plan.get('filters'):
        for filter_condition in query_plan['filters']:
            if filter_condition.get('dataset') == 'buildings':
                buildings_df = apply_filter(buildings_df, filter_condition)
            elif filter_condition.get('dataset') == 'financial':
                financial_df = apply_filter(financial_df, filter_condition)
    
    # Perform calculations
    if query_plan.get('calculations'):
        for calc in query_plan['calculations']:
            calc_result = perform_calculation(
                calc, 
                buildings_df, 
                financial_df, 
                query_plan.get('time_period')
            )
            results[calc['name']] = calc_result
    
    return results

def apply_filter(df: pd.DataFrame, filter_condition: Dict) -> pd.DataFrame:
    """
    Apply a filter condition to a DataFrame.
    """
    field = filter_condition.get('field')
    operator = filter_condition.get('operator')
    value = filter_condition.get('value')
    
    if operator == 'equals':
        return df[df[field] == value]
    elif operator == 'greater_than':
        return df[df[field] > value]
    elif operator == 'less_than':
        return df[df[field] < value]
    # Add more operators as needed
    
    return df

def perform_calculation(calc: Dict, buildings_df: pd.DataFrame, 
                       financial_df: pd.DataFrame, time_period: Dict) -> Any:
    """
    Perform a calculation based on the calculation type.
    """
    calc_type = calc.get('type')
    
    if calc_type == 'max':
        return calculate_max(calc, buildings_df, financial_df, time_period)
    elif calc_type == 'min':
        return calculate_min(calc, buildings_df, financial_df, time_period)
    elif calc_type == 'sum':
        return calculate_sum(calc, buildings_df, financial_df, time_period)
    elif calc_type == 'average':
        return calculate_average(calc, buildings_df, financial_df, time_period)
    elif calc_type == 'count':
        return calculate_count(calc, buildings_df, financial_df, time_period)
    elif calc_type == 'trend':
        return calculate_trend(calc, buildings_df, financial_df, time_period)
    
    return None

def parse_user_query(question: str) -> dict:
    """
    Parse the user's question to extract building ID, year, and cost type.
    """
    building_pattern = r"B\d{3}"
    year_pattern = r"\b20\d{2}\b"
    cost_type_pattern = r"(Energy Costs|Cleaning Costs|Utilities Costs|Maintenance Costs|Total Operating Expense)"

    building_id = re.search(building_pattern, question)
    year = re.search(year_pattern, question)
    cost_type = re.search(cost_type_pattern, question)

    return {
        "building_id": building_id.group(0) if building_id else None,
        "year": int(year.group(0)) if year else None,
        "cost_type": cost_type.group(0) if cost_type else None
    }

def parse_query_with_gpt(user_message: str, system_prompt: str) -> dict:
    """
    Use GPT to parse user queries into structured actions.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    return response.choices[0].message.content


def execute_query(parsed_query, buildings_df, financial_df):
    dataset = buildings_df if parsed_query["dataset"] == "buildings" else financial_df

    if parsed_query["action"] == "aggregate":
        if parsed_query["operation"] == "max":
            result = dataset.loc[dataset[parsed_query["column"]].idxmax()]
            return f"The most expensive building is {result['Building ID']} in {result['Location']} with a total operating expense of ${result[parsed_query['column']]:,}."
        elif parsed_query["operation"] == "count":
            return f"There are a total of {len(dataset)} entries in the {parsed_query['dataset']} dataset."
    elif parsed_query["action"] == "filter":
        # Implement filtering logic
        pass
    elif parsed_query["action"] == "compare":
        # Implement comparison logic
        pass

    return "Unsupported query type."

def calculate_max(calc: Dict, buildings_df: pd.DataFrame, 
                      financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate maximum value with context."""
    field = calc.get('field')
    dataset = calc.get('dataset', 'buildings')
    df = buildings_df if dataset == 'buildings' else financial_df
    
    if time_period:
        if 'year' in time_period:
            if dataset == 'financial':
                df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
            else:
                # For buildings dataset, no time filtering needed unless specifically looking at historical data
                pass
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    max_value = df[field].max()
    max_row = df.loc[df[field] == max_value].iloc[0]
    
    return {
        "value": max_value,
        "building_id": max_row.get('Building ID'),
        "location": max_row.get('Location') if 'Location' in max_row else None,
        "context": max_row.to_dict()
    }

def calculate_min(calc: Dict, buildings_df: pd.DataFrame, 
                 financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate minimum value with context."""
    field = calc.get('field')
    dataset = calc.get('dataset', 'buildings')
    df = buildings_df if dataset == 'buildings' else financial_df
    
    if time_period:
        if 'year' in time_period and dataset == 'financial':
            df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    min_value = df[field].min()
    min_row = df.loc[df[field] == min_value].iloc[0]
    
    return {
        "value": min_value,
        "building_id": min_row.get('Building ID'),
        "location": min_row.get('Location') if 'Location' in min_row else None,
        "context": min_row.to_dict()
    }

def calculate_sum(calc: Dict, buildings_df: pd.DataFrame, 
                 financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate sum with grouping options."""
    field = calc.get('field')
    dataset = calc.get('dataset', 'buildings')
    groupby = calc.get('groupby')
    df = buildings_df if dataset == 'buildings' else financial_df
    
    if time_period:
        if 'year' in time_period and dataset == 'financial':
            df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    if groupby:
        result = df.groupby(groupby)[field].sum().to_dict()
        return {
            "grouped_sums": result,
            "total": sum(result.values())
        }
    else:
        return {
            "total": df[field].sum()
        }

def calculate_average(calc: Dict, buildings_df: pd.DataFrame, 
                     financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate average with grouping options."""
    field = calc.get('field')
    dataset = calc.get('dataset', 'buildings')
    groupby = calc.get('groupby')
    df = buildings_df if dataset == 'buildings' else financial_df
    
    if time_period:
        if 'year' in time_period and dataset == 'financial':
            df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    if groupby:
        result = df.groupby(groupby)[field].mean().to_dict()
        return {
            "grouped_averages": result,
            "overall_average": df[field].mean()
        }
    else:
        return {
            "average": df[field].mean()
        }

def calculate_count(calc: Dict, buildings_df: pd.DataFrame, 
                   financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate count with grouping options."""
    field = calc.get('field')
    dataset = calc.get('dataset', 'buildings')
    groupby = calc.get('groupby')
    df = buildings_df if dataset == 'buildings' else financial_df
    
    if time_period:
        if 'year' in time_period and dataset == 'financial':
            df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    if groupby:
        result = df.groupby(groupby)[field].count().to_dict()
        return {
            "grouped_counts": result,
            "total_count": len(df)
        }
    else:
        return {
            "count": len(df)
        }

def calculate_trend(calc: Dict, buildings_df: pd.DataFrame, 
                   financial_df: pd.DataFrame, time_period: Dict) -> Dict:
    """Calculate trend over time."""
    field = calc.get('field')
    building_id = calc.get('building_id')
    df = financial_df  # Trends are always from financial data
    
    # Filter for specific building if provided
    if building_id:
        df = df[df['Building ID'] == building_id]
    
    # Apply time period filter
    if time_period:
        if 'year' in time_period:
            df = df[pd.to_datetime(df['Date']).dt.year == time_period['year']]
        if 'start_date' in time_period and 'end_date' in time_period:
            df = df[(df['Date'] >= time_period['start_date']) & 
                   (df['Date'] <= time_period['end_date'])]
    
    if df.empty:
        return {"error": "No data found for the specified criteria"}
    
    # Group by date and calculate statistics
    df['Date'] = pd.to_datetime(df['Date'])
    trend_data = df.groupby('Date')[field].agg(['mean', 'min', 'max']).reset_index()
    
    return {
        "dates": trend_data['Date'].tolist(),
        "values": trend_data['mean'].tolist(),
        "min_values": trend_data['min'].tolist(),
        "max_values": trend_data['max'].tolist(),
        "overall_trend": "increasing" if trend_data['mean'].is_monotonic_increasing else
                        "decreasing" if trend_data['mean'].is_monotonic_decreasing else
                        "fluctuating"
    }


def parse_user_query_with_gpt(user_message: str, system_prompt: str) -> dict:
    """
    Use GPT to parse user queries into structured actions.
    """
    messages = [
        {"role": "system", "content": system_prompt + "\n\nRespond ONLY with a valid JSON object. Make sure the JSON is properly formatted and contains the necessary query information."},
        {"role": "user", "content": user_message},
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2  # Make the response more consistent
        )
        
        # Extract the content and parse as JSON
        response_content = response.choices[0].message.content
        
        # Try to parse the JSON
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the text
            json_match = re.search(r'(\{.*?\})', response_content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    print(f"Could not parse JSON from: {response_content}")
                    return {"error": "Could not parse JSON response"}
            
            print(f"No JSON found in response: {response_content}")
            return {"error": "No valid JSON found in response"}
    
    except Exception as e:
        print(f"Error in parse_user_query_with_gpt: {e}")
        return {"error": str(e)}

def execute_data_query(query: dict, buildings_data: pd.DataFrame, financial_data: pd.DataFrame) -> Dict:
    """
    Execute the data query on the provided datasets.
    """
    if not isinstance(query, dict):
        raise ValueError("Query must be a dictionary")
    
    # Handle potential error from previous step
    if 'error' in query:
        return query
    
    # Check if query_plan exists
    if 'query_plan' not in query:
        # For queries without a detailed query plan, try to infer the intent
        return execute_flexible_query(query, buildings_data, financial_data)
    
    query_plan = query['query_plan']
    
    # Ensure calculations are present
    if 'calculations' not in query_plan or not query_plan['calculations']:
        # If no calculations, try flexible query approach
        return execute_flexible_query(query, buildings_data, financial_data)
    
    # Get the first calculation (assuming single calculation for now)
    calculation = query_plan['calculations'][0]
    
    # Mapping of calculation types to their respective functions
    calculation_map = {
        'min': calculate_min,
        'max': calculate_max,
        'count': calculate_count,
        'average': calculate_average,
        'sum': calculate_sum,
        'trend': calculate_trend
    }
    
    # Get the calculation function
    calc_func = calculation_map.get(calculation['type'])
    
    if not calc_func:
        raise ValueError(f"Unsupported calculation type: {calculation['type']}")
    
    # Perform the calculation
    result = calc_func({
        'field': calculation['field'],
        'dataset': calculation.get('dataset', 'buildings'),
        'building_id': calculation.get('building_id')
    }, buildings_data, financial_data, query_plan.get('time_period'))
    
    # Convert NumPy types to standard Python types
    result = convert_numpy_types(result)
    
    return {
        "result": result,
        "query": query
    }

import re
import pandas as pd
import numpy as np

def execute_flexible_query(query: dict, *dataframes: pd.DataFrame) -> Dict:
    """
    Dynamically analyze and process queries across multiple dataframes.
    
    Core principles:
    - No hard-coded questions
    - Flexible query interpretation
    - Generic data operations
    """
    user_query = query.get('user_query', '').lower()
    
    # Extract potential semantic elements
    elements = {
        'numeric_values': re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', user_query),
        'column_candidates': [],
        'operation_types': [],
        'grouping_candidates': []
    }
    
    # Dynamic column identification
    def identify_potential_columns(dataframes):
        all_columns = set()
        for df in dataframes:
            all_columns.update(df.columns)
        return [col for col in all_columns if any(word.lower() in col.lower() for word in user_query.split())]
    
    elements['column_candidates'] = identify_potential_columns(dataframes)
    
    # Semantic operation detection
    operation_map = {
        'count': ['how many', 'count', 'number of'],
        'sum': ['total', 'sum', 'aggregate'],
        'average': ['average', 'mean', 'typical'],
        'max': ['highest', 'maximum', 'largest', 'most'],
        'min': ['lowest', 'minimum', 'smallest', 'least']
    }
    
    elements['operation_types'] = [
        op for op, triggers in operation_map.items() 
        if any(trigger in user_query for trigger in triggers)
    ]
    
    # Fallback to first detected operation if none found
    if not elements['operation_types']:
        elements['operation_types'] = ['average']  # Default fallback
    
    # Dynamic filtering
    def apply_dynamic_filters(dataframes):
        filtered_dfs = []
        for df in dataframes:
            for col in elements['column_candidates']:
                # Try text-based filtering
                text_filters = [val for val in elements['numeric_values'] if val.isalpha()]
                if text_filters:
                    df = df[df[col].astype(str).str.contains('|'.join(text_filters), case=False)]
                
                # Try numeric filtering
                numeric_filters = [float(val.replace(',', '')) for val in elements['numeric_values'] if val.replace(',', '').isnumeric()]
                if numeric_filters:
                    df = df[df[col].isin(numeric_filters)]
            
            filtered_dfs.append(df)
        return filtered_dfs
    
    filtered_dataframes = apply_dynamic_filters(dataframes)
    
    # Generic data operation
    def perform_generic_operation(dataframes):
        results = {}
        for df in dataframes:
            for col in elements['column_candidates']:
                for op in elements['operation_types']:
                    try:
                        if op == 'count':
                            result = len(df)
                        elif op == 'sum':
                            result = df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else None
                        elif op == 'average':
                            result = df[col].mean() if pd.api.types.is_numeric_dtype(df[col]) else None
                        elif op == 'max':
                            result = df[col].max() if pd.api.types.is_numeric_dtype(df[col]) else None
                        elif op == 'min':
                            result = df[col].min() if pd.api.types.is_numeric_dtype(df[col]) else None
                        
                        if result is not None:
                            results[f"{op.capitalize()} of {col}"] = result
                    except Exception:
                        continue
        
        return results
    
    # Execute analysis
    analysis_results = perform_generic_operation(filtered_dataframes)
    
    return {
        "result": analysis_results,
        "query_interpretation": elements,
        "query": query
    }

def execute_data_query(query: dict, buildings_data: pd.DataFrame, financial_data: pd.DataFrame) -> Dict:
    """
    Execute the data query on the provided datasets.
    """
    if not isinstance(query, dict):
        raise ValueError("Query must be a dictionary")
    
    # Handle potential error from previous step
    if 'error' in query:
        return query
    
    # Check if query_plan exists
    if 'query_plan' not in query:
        # For queries without a detailed query plan, try to infer the intent
        return execute_flexible_query(query, buildings_data, financial_data)
    
    query_plan = query['query_plan']
    
    # Ensure calculations are present
    if 'calculations' not in query_plan or not query_plan['calculations']:
        # If no calculations, try flexible query approach
        return execute_flexible_query(query, buildings_data, financial_data)
    
    # Get the first calculation (assuming single calculation for now)
    calculation = query_plan['calculations'][0]
    
    # Mapping of calculation types to their respective functions
    calculation_map = {
        'min': calculate_min,
        'max': calculate_max,
        'count': calculate_count,
        'average': calculate_average,
        'sum': calculate_sum,
        'trend': calculate_trend
    }
    
    # Get the calculation function
    calc_func = calculation_map.get(calculation['type'])
    
    if not calc_func:
        return execute_flexible_query(query, buildings_data, financial_data)
    
    # Perform the calculation
    result = calc_func({
        'field': calculation['field'],
        'dataset': calculation.get('dataset', 'buildings'),
        'building_id': calculation.get('building_id')
    }, buildings_data, financial_data, query_plan.get('time_period'))
    
    # Convert NumPy types to standard Python types
    result = convert_numpy_types(result)
    
    return {
        "result": result,
        "query": query
    }

def generate_response_with_gpt(data_result: Dict, user_message: str, system_prompt: str) -> str:
    """
    Generate a natural language response using GPT.
    """
    # Ensure data_result is fully converted to JSON-serializable types
    result_str = json.dumps(convert_numpy_types(data_result), indent=2)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": f"Data Analysis Result: {result_str}"},
        {"role": "user", "content": "Based on this data result, provide a clear and concise natural language explanation. Focus on the key insights and make sure to include specific details from the result."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        
        # Extract content properly with new syntax
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in generate_response_with_gpt: {e}")
        return f"An error occurred while generating the response: {e}"