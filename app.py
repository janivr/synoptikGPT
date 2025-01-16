import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Basic error checking at startup
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set OPENAI_API_KEY in your .env file")
    st.stop()

try:
    # Test OpenAI client initialization
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    st.error(f"Error initializing OpenAI client: {str(e)}")
    st.stop()

# Try loading the data files
try:
    buildings_df = pd.read_csv('data/Buildings.csv')
    financial_df = pd.read_csv('data/Financial_Data.csv')
except Exception as e:
    st.error(f"Error loading data files: {str(e)}")
    st.stop()

# Main UI
st.title("Real Estate Portfolio Assistant")
st.write("Get insights about your properties and financial performance.")

# Display basic stats
st.write(f"Loaded {len(buildings_df)} buildings and {len(financial_df)} financial records.")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
question = st.chat_input("Ask about your portfolio:")

if question:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Process with GPT
    with st.chat_message("assistant"):
        try:
            with st.spinner("Analyzing..."):
                # Create context
                context = f"""Analyze this real estate portfolio data to answer the question.
                
                Building Summary:
                Total Buildings: {len(buildings_df)}
                Locations: {', '.join(buildings_df['Location'].unique())}
                Building Types: {', '.join(buildings_df['Purpose'].unique())}
                
                For the specific question: {question}
                """
                
                # Get GPT response
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": question}
                    ],
                    temperature=0
                )
                
                answer = response.choices[0].message.content
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")

# Clear chat button
with st.sidebar:
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()