from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import json
import re
from datetime import datetime

# OpenAI API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Data
@st.cache_data
def load_data():
    financial_data_df = pd.read_csv("Financial_Data.csv")
    buildings_df = pd.read_csv("Buildings.csv")
    financial_data_df['Date'] = pd.to_datetime(financial_data_df['Date'])
    return financial_data_df, buildings_df

financial_data_df, buildings_df = load_data()

def process_financial_query(question, financial_df):
    # Extract building ID, year, and month from question or context
    building_match = re.search(r'B\d{3}', question)
    year_match = re.search(r'20\d{2}', question)
    
    # Enhanced month matching to include numbers
    month_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2})', question, re.IGNORECASE)
    
    if building_match:
        building_id = building_match.group()
        building_data = financial_df[financial_df['Building ID'] == building_id]
        
        # Initialize empty results dictionary
        results = {'monthly_data': {}}
        
        if year_match:
            year = int(year_match.group())
            year_data = building_data[building_data['Date'].dt.year == year]
            
            # Get all months' data for the year
            for month in range(1, 13):
                month_data = year_data[year_data['Date'].dt.month == month]
                if not month_data.empty:
                    results['monthly_data'][month] = {
                        'Energy': round(month_data['Energy Costs (USD)'].sum(), 2),
                        'Clean': round(month_data['Cleaning Costs (USD)'].sum(), 2),
                        'Utils': round(month_data['Utilities Costs (USD)'].sum(), 2),
                        'Maint': round(month_data['Maintenance Costs (USD)'].sum(), 2),
                        'Total': round(month_data['Total Operating Expense (USD)'].sum(), 2)
                    }
            
            # Add yearly totals
            if not year_data.empty:
                results['yearly_total'] = {
                    'Energy': round(year_data['Energy Costs (USD)'].sum(), 2),
                    'Clean': round(year_data['Cleaning Costs (USD)'].sum(), 2),
                    'Utils': round(year_data['Utilities Costs (USD)'].sum(), 2),
                    'Maint': round(year_data['Maintenance Costs (USD)'].sum(), 2),
                    'Total': round(year_data['Total Operating Expense (USD)'].sum(), 2)
                }
            
            # If specific month is requested, add it to context
            if month_match:
                month = None
                try:
                    # Try to parse numeric month
                    month = int(month_match.group())
                except ValueError:
                    # Parse month name
                    month = datetime.strptime(month_match.group(), '%B').month
                
                if month in results['monthly_data']:
                    results['requested_month'] = {
                        'month': month,
                        'data': results['monthly_data'][month]
                    }
            
            return results
    return None

# Initialize session state for conversation history
if "messages" not in st.session_state:
    portfolio_stats = {
        'Total Buildings': int(len(buildings_df)),
        'By Region': {k: int(v) for k, v in buildings_df['Region'].value_counts().to_dict().items()},
        'By Ownership': {k: int(v) for k, v in buildings_df['Ownership'].value_counts().to_dict().items()},
        'LEED Certified': int(buildings_df['LEED Certified'].notna().sum())
    }
    
    buildings_info = []
    for _, row in buildings_df.iterrows():
        building_dict = {
            'ID': str(row['Building ID']),
            'Loc': str(row['Location']),
            'Size': f"{int(row['Size']):,}",
            'Use': str(row['Purpose']),
            'Own': str(row['Ownership'])
        }
        buildings_info.append(building_dict)

    min_year = financial_data_df['Date'].dt.year.min()
    max_year = financial_data_df['Date'].dt.year.max()

    system_prompt = f"""You are Sage, a head of real estate assistant. You have access to building and financial data.

Basic Portfolio Stats:
{json.dumps(portfolio_stats, indent=2)}

Building Details:
{json.dumps(buildings_info, indent=2)}

Your financial data includes monthly records with:
- Energy Costs (USD)
- Cleaning Costs (USD)
- Utilities Costs (USD)
- Maintenance Costs (USD)
- Total Operating Expense (USD)

IMPORTANT RULES:
1. When financial data is provided for a specific month/year, ONLY use that data
2. Do not reuse financial data from previous queries
3. If no financial data is provided for a specific month/year, clearly state that data is not available
4. Always include $ symbol and commas in financial numbers
5. Be precise about which month and year the data represents
6. Never make assumptions about missing months or years

Example good response: "The energy costs for Building B001 in March 2023 were $45,678"
Example good response: "I don't have data available for Building B001 in April 2023"
"""

    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

def ask_gpt_with_context(question):
    financial_result = process_financial_query(question, financial_data_df)
    if financial_result:
        # Format the context based on available data
        context_parts = ["\nIMPORTANT - Financial data details:"]
        
        # If a specific month was requested and data exists
        if 'requested_month' in financial_result:
            month_name = datetime.strptime(str(financial_result['requested_month']['month']), "%m").strftime("%B")
            data = financial_result['requested_month']['data']
            context_parts.append(f"\nData available for {month_name}:")
            context_parts.extend([
                f"- Energy Costs: ${data['Energy']:,.2f}",
                f"- Cleaning Costs: ${data['Clean']:,.2f}",
                f"- Utilities Costs: ${data['Utils']:,.2f}",
                f"- Maintenance Costs: ${data['Maint']:,.2f}",
                f"- Total Operating Expense: ${data['Total']:,.2f}"
            ])
        # If yearly data was requested
        elif 'yearly_total' in financial_result:
            data = financial_result['yearly_total']
            context_parts.append("\nYearly totals:")
            context_parts.extend([
                f"- Energy Costs: ${data['Energy']:,.2f}",
                f"- Cleaning Costs: ${data['Clean']:,.2f}",
                f"- Utilities Costs: ${data['Utils']:,.2f}",
                f"- Maintenance Costs: ${data['Maint']:,.2f}",
                f"- Total Operating Expense: ${data['Total']:,.2f}"
            ])
            
            # Add available months info
            available_months = sorted(financial_result['monthly_data'].keys())
            months_list = [datetime.strptime(str(m), "%m").strftime("%B") for m in available_months]
            context_parts.append(f"\nMonthly data available for: {', '.join(months_list)}")
        
        context = "\n".join(context_parts) + f"\n\nQuestion: {question}"
    else:
        context = question

    st.session_state.messages.append({"role": "user", "content": context})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages,
        max_tokens=1000
    )
    
    assistant_response = response.choices[0].message.content.strip()
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

# Streamlit App
st.title("Sage - Your Real Estate Portfolio Assistant")
st.markdown("Get strategic insights about your properties, financial performance, and portfolio optimization opportunities.")

# Display conversation history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# User Input
question = st.chat_input("Ask Sage about your real estate portfolio:")

if question:
    # Query GPT and display response
    with st.chat_message("user"):
        st.write(question)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your portfolio..."):
            answer = ask_gpt_with_context(question)
            st.write(answer)

# Clear chat button in sidebar
with st.sidebar:
    if st.button("Clear Chat"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()