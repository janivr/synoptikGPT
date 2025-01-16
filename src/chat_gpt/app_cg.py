import streamlit as st
import pandas as pd
from openai import OpenAI, OpenAIError
import os
import logging
from dotenv import load_dotenv
import time
import requests
import airtable 
import io

# Load OpenAI API Key and Airtable API Key from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
airtable_api_key = os.getenv("AIRTABLE_API_KEY")
airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
airtable_token = os.getenv("AIRTABLE_TOKEN")

if not airtable_api_key or not airtable_base_id:
    raise ValueError("Airtable API key or Base ID is missing from environment variables.")

client = OpenAI(api_key=openai_api_key)

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

# Initialize session state
if "data_loaded" not in st.session_state:
    st.session_state.update({
        "data_loaded": False,
        "datasets": {},
        "chat_history": [],
        "thread_id": None,
        "assistant_id": None
    })

# Airtable setup
airtable_client = airtable.Airtable(airtable_base_id, airtable_api_key)
buildings_table = airtable.Airtable(airtable_base_id, 'Buildings', airtable_token)
financial_table = airtable.Airtable(airtable_base_id, 'Financial_Data', airtable_token)

print(f"Airtable API Key: {'*' * len(airtable_api_key) if airtable_api_key else 'Not set'}")
print(f"Airtable Base ID: {airtable_base_id if airtable_base_id else 'Not set'}")
print(f"Airtable Token: {airtable_token[:5]}...{airtable_token[-5:] if airtable_token else 'Not set'}")

def load_csv_datasets(data_folder="data"):
    datasets = {}
    try:
        for file_name in os.listdir(data_folder):
            if file_name.endswith(".csv"):
                dataset_name = os.path.splitext(file_name)[0]
                file_path = os.path.join(data_folder, file_name)
                datasets[dataset_name] = pd.read_csv(file_path)
                logging.info(f"Loaded dataset: {dataset_name}, Shape: {datasets[dataset_name].shape}")
        return datasets
    except Exception as e:
        logging.error(f"Error loading datasets: {e}")
        st.error(f"Error loading datasets: {e}")
        return {}



def test_airtable_api():
    url = f"https://api.airtable.com/v0/{airtable_base_id}/Buildings"
    headers = {
        "Authorization": f"Bearer {airtable_api_key}",
        "Content-Type": "application/json"
    }
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    response = requests.get(url, headers=headers)
    print(f"Airtable API Response: {response.status_code}")
    print(f"Response content: {response.text[:500]}...")  # Print first 500 characters of response
    
def test_airtable_connection():
    try:
        records = airtable_client.get('Buildings')
        print(f"Successfully connected to Airtable. Sample record: {records[0] if records else 'No records found'}")
    except Exception as e:
        print(f"Error connecting to Airtable: {str(e)}")

#test_airtable_connection()
#test_airtable_api()

def load_datasets_from_airtable():
    datasets = {}
    try:
        # Load Buildings dataset
        buildings_data = airtable_client.get('Buildings')
        buildings_df = pd.DataFrame([record['fields'] for record in buildings_data['records']])
        print(f"Buildings dataset loaded. Shape: {buildings_df.shape}")
        print(f"Columns: {buildings_df.columns}")
        datasets["Buildings"] = buildings_df

        # Load Financial Data dataset with pagination
        financial_records = []
        offset = None
        while True:
            financial_data = airtable_client.get('Financial Data', offset=offset)
            financial_records.extend(financial_data['records'])
            offset = financial_data.get('offset')
            if not offset:
                break

        financial_df = pd.DataFrame([record['fields'] for record in financial_records])
        print(f"Financial dataset loaded. Shape: {financial_df.shape}")
        print(f"Columns: {financial_df.columns}")
        datasets["Financial Data"] = financial_df

        return datasets
    except Exception as e:
        logging.error(f"Error loading datasets from Airtable: {str(e)}")
        logging.error(f"Error type: {type(e)}")
        logging.error(f"Error details: {str(e)}")
        st.error(f"Error loading datasets from Airtable: {str(e)}")
        return {}

    
def list_airtable_tables():
    try:
        url = f"https://api.airtable.com/v0/meta/bases/{airtable_base_id}/tables"
        headers = {
            "Authorization": f"Bearer {airtable_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tables = response.json().get('tables', [])
            print("Available tables:")
            for table in tables:
                print(f"- {table['name']}")
        else:
            print(f"Error listing tables: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error listing tables: {str(e)}")

# Call this function before loading datasets
list_airtable_tables()

def upload_datasets_to_assistant(datasets):
    try:
        # Upload datasets as files
        file_ids = []
        for name, df in datasets.items():
            csv_data = df.to_csv(index=False).encode()
            file = client.files.create(
                file=io.BytesIO(csv_data),
                purpose='assistants'
            )
            file_ids.append(file.id)
            logging.info(f"Uploaded {name} dataset. File ID: {file.id}")

        # Create an assistant
        assistant = client.beta.assistants.create(
            name="Real Estate Data Assistant",
            description="You analyze real estate data from CSV files, understand trends, and provide insights. You also perform calculations and answer questions based on the data.",
            model="gpt-4-turbo",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                    "file_ids": file_ids
                }
            },
            instructions=(
                "You are an expert assistant for analyzing real estate data. "
                "Use the complete datasets provided to answer questions about the data. "
                "Always show your work, including data analysis steps and any calculations performed. "
                "When performing mathematical operations, use precise arithmetic and double-check your calculations."
                 "You are an expert assistant for analyzing real estate data. "
                "Use the complete datasets I provide to answer questions about the data."
                f"The Buildings dataset contains {len(datasets['Buildings'])} records. "
                f"The Financial Data dataset contains {len(datasets['Financial Data'])} records. "                
                "When analyzing the airtable data or any similar dataset:\n"
                "1. Always read and process the entire dataset, not just a sample.\n"
                "2. For questions about counts or maximums, always verify your results by listing specific examples.\n"
                "3. Show your work in detail, including intermediate steps in your calculations.\n"
                "4. Identify max, avg, sum, min, mean, count, including ties for all number fields.\n"
                "5. When performing mathematical operations, always use precise arithmetic. Double-check your calculations, and if possible, use built-in mathematical functions for accuracy.\n"
                "6. For large sums, break the calculation into groups of 5-10 numbers, sum each group, then sum the results of these groups.\n"
                "7. After calculating a sum, verify the result by adding the numbers in reverse order or by using a different grouping method.\n"
                "8. If your calculated sum differs significantly from the sum of the individual numbers you've listed, flag this discrepancy and recalculate.\n"
                "9. Use precise arithmetic and avoid rounding.\n"
            )
        )
        st.session_state["assistant_id"] = assistant.id
        logging.info(f"Created assistant with ID: {assistant.id}")

        # Create a thread
        thread = client.beta.threads.create()
        thread_id = thread.id
        logging.info(f"Created thread: {thread_id}")

        return thread_id
    except Exception as e:
        logging.error(f"Error uploading datasets and creating assistant: {e}")
        st.error(f"Error uploading datasets and creating assistant: {e}")
        return None
    


    
def upload_datasets_to_assistant_files(datasets):
    """Upload datasets to the assistant using file upload capabilities"""
    try:
        # Create an assistant
        assistant = client.beta.assistants.create(
            name="Real Estate Data Assistant",
            instructions=(
                "You are an expert assistant for analyzing real estate data. "
                "Use the datasets I provide to answer questions about the data."
            ),
            model="gpt-4-1106-preview"
        )
        st.session_state["assistant_id"] = assistant.id

        # Create a thread
        thread_response = client.beta.threads.create()
        thread_id = thread_response.id
        logging.info(f"Created thread: {thread_id}")

        # Upload datasets to the thread
        for name, df in datasets.items():
            csv_data = df.to_csv(index=False)
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                attachments=[
                    {
                        "filename": f"{name}.csv",
                        "content_type": "text/csv",
                        "binary_data": csv_data.encode()
                    }
                ]
            )
            logging.info(f"Uploaded dataset: {name}")

        # Verify that all files were uploaded successfully
        messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc").data
        uploaded_files = [msg.attachments[0].filename for msg in messages if msg.attachments]
        if len(uploaded_files) == len(datasets):
            logging.info("All datasets uploaded successfully.")
            return thread_id
        else:
            logging.error("Some datasets failed to upload.")
            return None
    except Exception as e:
        logging.error(f"Error uploading datasets: {e}")
        st.error(f"Error uploading datasets: {e}")
        return None
    
def verify_city_field(buildings_df):
    if "City" not in buildings_df.columns:
        logging.error("The 'City' field is missing in the Buildings dataset.")
        st.error("The 'City' field is missing in the Buildings dataset.")
        return None
    logging.info("'City' field is present in the dataset.")
    ny_buildings = buildings_df[buildings_df["City"].str.contains("New York", na=False)]
    logging.info(f"Found {len(ny_buildings)} buildings in New York.")
    return ny_buildings


    
import time
from openai import OpenAIError

def process_query(thread_id, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Create a message in the thread
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=query
            )
            logging.info(f"Sent query to thread. Message ID: {message.id}")

            # Create a run
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=st.session_state["assistant_id"]
            )
            logging.info(f"Created run with ID: {run.id}")

            # Wait for the run to complete
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )
                logging.info(f"Run status: {run_status.status}")
                if run_status.status == "completed":
                    # Retrieve messages
                    messages = client.beta.threads.messages.list(
                        thread_id=thread_id, order="desc"
                    ).data
                    for msg in messages:
                        if msg.role == "assistant":
                            logging.info(f"Assistant response: {msg.content}")
                            return msg.content[0].text.value
                    return "No response from assistant."
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    raise Exception(f"Run failed, cancelled, or expired: {run_status.status}")
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error during query processing: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return f"An unexpected error occurred: {str(e)}"

    return "Failed to process query after maximum retries."

# Streamlit UI
st.set_page_config(page_title="Real Estate Assistant", layout="wide")
st.title("Real Estate Assistant AI")

if not st.session_state["data_loaded"]:
    datasets = load_datasets_from_airtable()
    if datasets.get("Buildings") is not None:
        ny_buildings = verify_city_field(datasets["Buildings"])
        if ny_buildings is not None:
            st.write(f"Number of buildings in New York: {len(ny_buildings)}")
    if datasets:
        st.session_state["thread_id"] = upload_datasets_to_assistant(datasets)
        st.session_state["data_loaded"] = True
        total_records = sum(len(df) for df in datasets.values())
        st.write(f"Successfully uploaded {total_records} records to ChatGPT.")               
            
    else:
        st.error("Failed to load any datasets from Airtable.")



def send_query():
    if st.session_state.query.strip():
        answer = process_query(
            st.session_state["thread_id"], 
            st.session_state.query
        )
        st.session_state["chat_history"].append({"user": st.session_state.query, "ai": answer})
        st.session_state.query = ""

col1, col2 = st.columns([3, 1])
with col1:
    st.text_input("Enter your question:", key="query", on_change=send_query)
with col2:
    st.button("Send", on_click=send_query)

# Display chat history
st.sidebar.title("Chat History")
for msg in reversed(st.session_state.get("chat_history", [])):
    st.sidebar.markdown(f"**User**: {msg['user']}")
    st.sidebar.markdown(f"**AI**: {msg['ai']}")

if st.checkbox("Show Logs (Admin Only)"):
    try:
        with open(LOG_FILE, "r") as log_file:
            logs = log_file.readlines()
            st.text_area("Logs", value="".join(logs[-100:]), height=300)
    except FileNotFoundError:
        st.error("Log file not found.")
    except Exception as e:
        st.error(f"Error displaying logs: {e}")
        
