import streamlit as st
import pandas as pd
import os
import logging
import time
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

# Load environment variables
load_dotenv()

# Logging Configuration
LOG_FILE = "app_log.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# read version 
with open("version.txt", "r") as f:
    app_version = f.read().strip()
    
# Console logging setup
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# OpenAI Initialization
#openai_api_key = st.secrets["OPENAI_API_KEY"]
openai_api_key = os.getenv("OPENAI_API_KEY")
#openai_api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
#openai_api_key = st.secrets["OPENAI_API_KEY"]
#print("Loaded API Key:", st.secrets["OPENAI_API_KEY"])

if not openai_api_key:
    raise ValueError("OpenAI API key is missing from environment variables.")
client = OpenAI(api_key=openai_api_key)

def init_db():
    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  user_input TEXT,
                  assistant_response TEXT)''')
    conn.commit()
    conn.close()

def save_interaction(user_input, assistant_response):
    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO interactions (timestamp, user_input, assistant_response) VALUES (?, ?, ?)",
              (timestamp, user_input, assistant_response))
    conn.commit()
    conn.close()
    
def get_interactions(limit=100):
    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    c.execute("SELECT * FROM interactions ORDER BY timestamp DESC LIMIT ?", (limit,))
    interactions = c.fetchall()
    conn.close()
    return interactions

# Retrieve interactions by a filter (e.g., by date)
def get_interactions_by_date(date):
    # USAGE: date = "2025-01-16"  
    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    c.execute('SELECT * FROM interactions WHERE timestamp LIKE ?', (f'{date}%',))
    rows = c.fetchall()
    conn.close()
    return rows

# Metadata Descriptions
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
}

financial_metadata = {
    "Record ID": "Unique identifier for each financial record.",
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

floors_occupancy_metadata = {
    "Building ID": "Unique identifier for each building.",
    "Floor": "The floor number within the building.",
    "Max Capacity": "Maximum number of occupants the floor can accommodate.",
}

def poll_run_status(thread_id, run_id, max_retries=10, initial_delay=1):
    delay = initial_delay
    for attempt in range(max_retries):
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        if run_status.status == 'completed':
            return True
        if run_status.status in ['failed', 'cancelled']:
            return False
        time.sleep(delay)
        delay *= 2  # Exponential backoff
    return False

@st.cache_data
def cached_analysis(query, thread_id, assistant_id):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    if query_hash in st.session_state.get('query_cache', {}):
        return st.session_state['query_cache'][query_hash]
    result = perform_analysis(query, thread_id, assistant_id)
    if 'query_cache' not in st.session_state:
        st.session_state['query_cache'] = {}
    st.session_state['query_cache'][query_hash] = result
    return result

def perform_analysis(query, thread_id, assistant_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=query
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    if poll_run_status(thread_id, run.id):
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value
    return "Unable to get a response from the assistant."

# Upload CSV Files from 'data' Folder
def upload_csv_files(data_folder="data"):
    file_ids = []
    try:
        for file_name in os.listdir(data_folder):
            if file_name.endswith(".csv"):
                file_path = os.path.join(data_folder, file_name)
                with open(file_path, "rb") as file:
                    uploaded_file = client.files.create(
                        file=file,
                        purpose='assistants'
                    )
                    file_ids.append(uploaded_file.id)
                    logging.info(f"Who Uploaded {file_name}. File ID: {uploaded_file.id}")

        return file_ids
    except Exception as e:
        logging.error(f"Error uploading files: {e}")
        st.error(f"Error uploading files: {e}")
        return []

# Create OpenAI Assistant
def create_assistant_with_uploaded_files(file_ids, metadata):
    try:
        metadata_info = "\n".join([f"- {key}: {value}" for key, value in metadata.items()])
        assistant = client.beta.assistants.create(
            name="Real Estate Data Assistant",
            description="Analyzes real estate data and answers questions based on uploaded datasets.",
            model="gpt-4-1106-preview",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                    "file_ids": file_ids
                }
            },
            instructions=(
                "You are Sage, a data analysis assistant specializing in real estate datasets. Use the following metadata to understand the datasets:\n" +
                metadata_info +
                "Provide concise and direct answers unless further clarification is requested." +
                "Format financial values with currency symbols and commas" + 
                "Avoid detailed explanations for straightforward questions." + 
                "Include relevant building details (location, size, purpose)" +
                "Explain any trends or patterns observed" +
                "\nUse this information to answer questions about building attributes, financial data, occupancy, energy , maintenance and trends. Provide accurate answers."

            )
        )
        logging.info(f"Created assistant with ID: {assistant.id}")
        return assistant
    except Exception as e:
        logging.error(f"Error creating assistant: {e}")
        st.error(f"Error creating assistant: {e}")
        return None

# Chat Interface for Users
def chat_with_assistant(assistant_id):
    
    # Initialize the database
    init_db()  
    
    st.header("Chat with the Real Estate Assistant")
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    st.subheader("Chat History")
    for message in st.session_state.messages:
        role = "You" if message["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {message['content']}")

    # Add some space between history and input
    st.markdown("---")

    # Create a form for input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask your question:", key="user_input")
        with col2:
            send_button = st.form_submit_button("Send")
            
    # Add some vertical spacing to align the button
    st.markdown("<style>div.stButton > button:first-child { margin-top: 25px; }</style>", unsafe_allow_html=True)
    
    if send_button and user_input:
        process_input(user_input, assistant_id)

    # Ensure focus stays at the bottom
    st.markdown('<div id="bottom-anchor"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <script>
            var element = document.getElementById('bottom-anchor');
            element.scrollIntoView();
        </script>
        """,
        unsafe_allow_html=True
    )

def process_input(user_input, assistant_id):
    with st.spinner('Assistant is thinking...'):
        try:
            response = cached_analysis(user_input, st.session_state["thread_id"], assistant_id)
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save the interaction to the database
            save_interaction(user_input, response)
            
        except Exception as e:
            logging.error(f"Error during conversation: {e}")
            st.error(f"Error during conversation: {e}")
    
    # Use Streamlit's rerun method to update the chat history
    st.rerun()

def admin_dashboard():
    st.title("Admin Dashboard")

    # Get date range for analysis
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    conn = sqlite3.connect('user_interactions.db')
    c = conn.cursor()
    
    # Count total interactions
    c.execute("SELECT COUNT(*) FROM interactions WHERE date(timestamp) BETWEEN ? AND ?", 
              (start_date, end_date))
    total_interactions = c.fetchone()[0]
    st.write(f"Total Interactions: {total_interactions}")

    # Most common user queries (example)
    c.execute("""
        SELECT user_input, COUNT(*) as count 
        FROM interactions 
        WHERE date(timestamp) BETWEEN ? AND ?
        GROUP BY user_input 
        ORDER BY count DESC 
        LIMIT 5
    """, (start_date, end_date))
    common_queries = c.fetchall()
    
    st.subheader("Most Common User Queries")
    for query, count in common_queries:
        st.write(f"{query}: {count}")

    conn.close()

def authenticate_admin_OLD_DELETE():
    token = st.text_input("Enter admin token", type="password")
    if token == st.secrets["admin"]["access_token"]:
        st.success("Authentication successful!")
        return True
    else:
        st.warning("Invalid token. Access denied.")
        return False

def authenticate_admin():
    # Initialize the admin state if not already done
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False
        st.session_state["admin_key_input"] = ""

    if not st.session_state["is_admin"]:
        # Display the input and button if not authenticated
        admin_key_input = st.text_input("Enter admin token", type="password", key="admin_key_input")
        if st.button("Submit Admin Token"):
            if admin_key_input == st.secrets["admin"]["access_token"]:  # Verify token
                st.session_state["is_admin"] = True
                st.success("Authentication successful!")
            else:
                st.error("Invalid token. Access denied.")
    else:
        st.success("You are logged in as Admin.")  # Show success message after authentication

    return st.session_state["is_admin"]


def download_database():
    db_path = 'user_interactions.db'
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            st.download_button(
                label="Download Database",
                data=f,
                file_name='user_interactions.db',
                mime='application/octet-stream'
            )
    else:
        st.warning("Database file not found.")


    
# Streamlit UI
st.set_page_config(page_title="Real Estate Assistant", layout="wide")
st.title("Real Estate Assistant AI")

# Load total interactions from database
if "total_requests" not in st.session_state:
        conn = sqlite3.connect('user_interactions.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM interactions")
        st.session_state["total_requests"] = c.fetchone()[0]
        conn.close()
        
# Display version in the sidebar
st.sidebar.markdown(f"### Version: {app_version}")
st.sidebar.markdown(f"### Total Requests: {st.session_state['total_requests']}")


# Upload and Process Datasets
if not st.session_state.get("data_uploaded"):
    file_ids = upload_csv_files()
    if file_ids:
        st.session_state["file_ids"] = file_ids
        st.session_state["data_uploaded"] = True
        st.write(f"Uploaded {len(file_ids)} datasets.")
    else:
        st.error("Failed to upload datasets.")

# Create Assistant
if st.session_state.get("data_uploaded"):
    if "assistant_id" not in st.session_state:
        assistant = create_assistant_with_uploaded_files(
            st.session_state["file_ids"],
            {**buildings_metadata, **financial_metadata, **floors_occupancy_metadata}
        )
        if assistant:
            st.session_state["assistant_id"] = assistant.id
            st.write("Assistant created successfully!")

# Chat Interface
if "assistant_id" in st.session_state:
    chat_with_assistant(st.session_state["assistant_id"])
    
    # Increment total request count
    st.session_state["total_requests"] += 1


# Sidebar Admin Login
with st.sidebar:
    st.title("Admin Panel")
    if authenticate_admin():
        st.success("Admin authenticated")
        # Admin features in the sidebar (e.g., download DB, version control)
        if st.button("Download Database"):
            download_database()
    else:
        st.warning("Admin access denied. Please authenticate.")
            


    
