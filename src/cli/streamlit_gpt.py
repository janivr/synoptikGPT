import streamlit as st
import sqlite3
import logging
import os
import sys
from datetime import datetime, timedelta
from chat_gpt.gpt_sql import (
    analyze_data_with_gpt,
    generate_sql_query,
    execute_validated_query,
    calculate_success_rate
)

QUESTION_COLOR = "#0056D6"  # A shade of blue
ANSWER_COLOR = "#009624"    # A shade of green

# Limit the size of chat_history to the last N entries
MAX_CHAT_HISTORY = 10
MAX_CHAT_HISTORY_AGE = timedelta(minutes=30)  # Keep entries from the last 30 minutes

# Initialize session states
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
# Logging Configuration
LOG_FILE = "app_log.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# Read version from version.txt
with open("version.txt", "r") as f:
    app_version = f.read().strip()


def authenticate_admin():
    # Initialize the admin state if not already done
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False
        st.session_state["admin_key_input"] = ""

    if not st.session_state["is_admin"]:
        # Display the input and button if not authenticated
        admin_key_input = st.sidebar.text_input("Enter admin token", type="password", key="admin_key_input")
        if st.sidebar.button("Submit Admin Token"):
            if admin_key_input == st.secrets["admin"]["access_token"]:  # Verify token
                st.session_state["is_admin"] = True
                st.sidebar.success("Authentication successful!")
            else:
                st.sidebar.error("Invalid token. Access denied.")
    else:
        st.sidebar.success("You are logged in as Admin.")  # Show success message after authentication
    return st.session_state["is_admin"]

def download_database():
    """Function to download the database"""
    try:
        with open('user_interactions.db', 'rb') as f:
            db_bytes = f.read()
            st.sidebar.download_button(
                label="Download Database",
                data=db_bytes,
                file_name="user_interactions.db",
                mime="application/octet-stream"
            )
    except Exception as e:
        st.sidebar.error(f"Error downloading database: {e}")

    
def add_to_chat_history(question, sql_query, answer):
    """Add a Q&A pair to chat history"""
    st.session_state.chat_history.append({
        "timestamp": datetime.now(),
        "question": question,
        "sql_query": sql_query,
        "answer": answer
    })
    
    st.session_state.chat_history = [
        entry for entry in st.session_state.chat_history
        if datetime.now() - entry["timestamp"] <= MAX_CHAT_HISTORY_AGE
    ]


def update_total_requests():
    """Update total requests in database and session state"""
    try:
        conn = sqlite3.connect('user_interactions.db')
        c = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO interactions (timestamp) VALUES (?)", (timestamp,))
        conn.commit()
        st.session_state["total_requests"] += 1
        conn.close()        
    except Exception as e:
        logging.error(f"Error updating total requests: {e}")

def log_query_analytics(query, outcome):
    with open("query_analytics.log", "a") as f:
        f.write(f"{datetime.now()} | Query: {query} | Outcome: {outcome}\n")

def display_history(history):
    st.markdown("### Chat History")
    for item in history:
        question_html = f"""
        <div style="color: {QUESTION_COLOR}; font-weight: bold; margin-bottom: 5px;">
            Q: {item['question']}
        </div>
        """
        answer_html = f"""
        <div style="color: {ANSWER_COLOR}; margin-bottom: 10px;">
            A: {item['answer']}
        </div>
        """
        st.markdown(question_html, unsafe_allow_html=True)
        st.markdown(answer_html, unsafe_allow_html=True)
        
# Streamlit UI
st.set_page_config(page_title="Real Estate Assistant", layout="wide")
st.title("Synoptik Real Estate Assistant AI")

    
# Load total interactions from the database
if "total_requests" not in st.session_state:
    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM interactions")
    st.session_state["total_requests"] = c.fetchone()[0]
    conn.close()

        
# Display version in the sidebar
st.sidebar.markdown(f"### Version: {app_version}")
st.sidebar.markdown(f"### Total Requests: {st.session_state['total_requests']}")

# Chat Interface
st.header("Ask Your Questions")
st.write("Use the assistant to ask questions about your real estate data.")
st.markdown("Examples:")
st.markdown("- **What is the total occupancy for all buildings in NYC?**")
st.markdown("- **List all buildings with energy costs over $10,000.**")

# Chat history display
chat_container = st.container()
with chat_container:
    for i, qa in enumerate(st.session_state.chat_history[:-1] if len(st.session_state.chat_history) > 1 else []):
        st.markdown(
            f"<p style='color:{QUESTION_COLOR}; '>Q: {qa['question']}</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{ANSWER_COLOR};  '>A: {qa['answer']}</p>",
            unsafe_allow_html=True
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("---")
        
# Latest Answer (if exists)
if st.session_state.chat_history:
    latest = st.session_state.chat_history[-1]
    st.markdown(
        f"<p style='color:{QUESTION_COLOR}; font-weight:bold;'>Q: {latest['question']}</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:{ANSWER_COLOR}; font-weight:bold; '>A: {latest['answer']}</p>",
        unsafe_allow_html=True
    )

# Initialize session state
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []
    
# Query Input and Execution
query_container = st.container()
with query_container:
    with st.form(key=f'query_form_{st.session_state.form_counter}'):
        user_query = st.text_area(
            "Enter your question (e.g., 'What is the average energy cost for buildings in New York?'):",
            key=f"query_input_{st.session_state.form_counter}"
        )
        submit_button = st.form_submit_button("Run Query")        

    if submit_button and user_query.strip():
        try:
            with st.spinner("Processing your query..."):
                
                conversation_context = "\n".join(
                    [f"Q: {qa['question']}\nA: {qa['answer']}" for qa in st.session_state.chat_history]
                )

                # Generate and execute SQL query silently
                sql_query = generate_sql_query(user_query,
                                               prev_context=st.session_state.conversation_context)                
                
                result = execute_validated_query(sql_query)
                
                log_query_analytics(sql_query, "Success")

                if "error" in result:
                    st.error(f"Query Failed: {result['details']}")
                    answer = f"Error: {result['error']}"
                elif not result["rows"]:
                    st.warning("No data found for your query.")
                    answer = "No data found"
                else:
                    answer = analyze_data_with_gpt(
                        user_query,
                        result["columns"],
                        result["rows"],
                        prev_context=st.session_state.conversation_context
                    )
                    st.success(answer)                    

                # Update counter and history
                update_total_requests()
                add_to_chat_history(user_query, sql_query, answer)
                
                # Reset form
                st.session_state.form_counter += 1
                st.rerun()

        except Exception as e:
            st.error("An error occurred. Please try a different question.")
            logging.error(f"Error in Streamlit app: {e}")

with st.sidebar:
    st.title("Analytics")
    success_rate = calculate_success_rate()
    st.metric("Query Success Rate", f"{success_rate:.2f}%")

# Sidebar Admin Login
with st.sidebar:
    st.title("Admin Panel")
    if authenticate_admin():
        download_database()
