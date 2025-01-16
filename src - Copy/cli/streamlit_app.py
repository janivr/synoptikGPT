import streamlit as st
from src.utils.data_loader import DataLoader
from src.modules.buildings import BuildingsModule
from src.modules.financial import FinancialModule
from src.utils.gpt_helper import create_system_prompt, ask_gpt
from src.utils.gpt_helper import ask_gpt

from src.utils.gpt_helper import (
    parse_user_query_with_gpt,
    execute_data_query,
    generate_response_with_gpt
)

# Load data
buildings_df = DataLoader.load_buildings_data()
financial_df = DataLoader.load_financial_data()

# Initialize modules
buildings_module = BuildingsModule(buildings_df)
financial_module = FinancialModule(financial_df)

# Debugging: Verify data is loaded properly
print(financial_module.data.head())
print(buildings_module.data.head())

# Initialize session state for conversation history
if "messages" not in st.session_state:
    system_prompt = create_system_prompt(buildings_module, financial_module)
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

# Streamlit App
st.title("Sage - Your Real Estate Portfolio Assistant")
st.markdown("Get strategic insights about your properties, financial performance, and portfolio optimization opportunities.")

# Display conversation history
for message in st.session_state.messages[1:]:  # Skip system message
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input
question = st.chat_input("Ask Sage about your real estate portfolio:")

if question:
    # Add user question to chat history
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Display user question
    with st.chat_message("user"):
        st.write(question)
    
    # Get GPT response
    #with st.chat_message("assistant"):
    #    with st.spinner("Analyzing your portfolio..."):
    #        # gpt_response = ask_gpt(st.session_state.messages)
    #        gpt_response = ask_gpt(st.session_state.messages, buildings_module, financial_module)
    #        st.write(gpt_response)

    # Get GPT response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your portfolio..."):
            try:
                # Step 1: Parse the query
                structured_query = parse_user_query_with_gpt(
                    user_message=question,
                    system_prompt=st.session_state.messages[0]["content"]
                )

                print("Parsed Query:", structured_query)  # Debugging output
                
                # Step 2: Execute the query on the data
                query_result = execute_data_query(
                    query=structured_query,
                    buildings_data=buildings_module.data,
                    financial_data=financial_module.data
                )
                
                print("Execute Query Input:", query_result) 

                # Step 3: Generate a natural language response
                gpt_response = generate_response_with_gpt(
                                    data_result=query_result,  
                                    system_prompt=st.session_state.messages[0]["content"],
                                    user_message=question
                                )
                print("Execute Response:",gpt_response)
                
                st.write(gpt_response)

            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.write(error_message)
                gpt_response = error_message
    
    # Add GPT response to chat history
    st.session_state.messages.append({"role": "assistant", "content": gpt_response})

# Clear chat button in sidebar
with st.sidebar:
    if st.button("Clear Chat"):
        st.session_state.messages = [st.session_state.messages[0]]  # Keep only system message
        st.rerun()