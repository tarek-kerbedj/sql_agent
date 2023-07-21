from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
import streamlit as st

def clean_answer(full_response):
    """Clean and sanitize the LLM response.

    This function takes a full_response string as input and performs the following
    cleaning operations:
    1. Replaces double quotes (") with single quotes (') for better consistency.
    2. Removes the phrase 'Final answer here' from the string.
    3. Replaces colons (:) with spaces for improved readability.

    Parameters:
    -----------
    full_response : str
        The input string containing the full response that needs to be cleaned.

    Returns:
    --------
    str
        The cleaned and sanitized version of the input full_response string.
    """
    full_response=full_response.replace('"',"'")
    full_response=full_response.replace('Final answer here',"")
    full_response=full_response.replace(':'," ")
    return full_response

def load_db(PROMPT,uri):
    """
    Establishes a connection to a SQL database and creates a SQLDatabaseChain instance.

    This function takes a prompt and a database URI, creates a SQLDatabase instance using the URI, 
    and then creates a SQLDatabaseChain instance using the prompt and the database.
    The SQLDatabaseChain is created with a ChatOpenAI instance with a temperature of 0.

    Parameters:
        PROMPT (str): The prompt to be used for the SQLDatabaseChain.
        uri (str): The URI of the database to connect to.

    Returns:
    SQLDatabaseChain: A SQLDatabaseChain instance connected to the specified database."""
    db=SQLDatabase.from_uri(uri)
    db_chain = SQLDatabaseChain.from_llm(ChatOpenAI(temperature=0), db, verbose=True,prompt=PROMPT,return_intermediate_steps=True)
    return db_chain
def show_messages(messages):
    """
    Iterates through a list of messages and displays them in a chat format.
    Parameters:
        messages (list): A list of messages to be displayed. Each message is expected to be a 
                        dictionary with at least two keys: 'role' and 'content'.
                        'role' is used to set the role of the chat message and 'content' is the actual 
                        message content to be displayed."""
    for message in messages:

        with st.chat_message(message["role"]):
            if type(message['content'])==str:
                st.markdown(message["content"],unsafe_allow_html=True)
            
            else:
                st.plotly_chart(message['content'], use_container_width=True)
def calculate_price(cb):
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}")