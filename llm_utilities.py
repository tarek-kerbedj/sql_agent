import json
import re
import os
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain import SQLDatabaseChain
import streamlit as st

os.environ["DB_STRING"]=st.secrets.DB_STRING

from langchain.prompts.prompt import PromptTemplate
from plotly.graph_objs import Figure
import plotly.graph_objects as go

def preprocess_visuals(full_response):
    """takes a string representation of a json that contains a plotly chart and returns a plotly figure object
        Parameters:
    -----------
    full_response : str
        The input string containing the full response that needs to parsed and turned into a json.

    Returns:
    --------
        fig : plotly.graph_objects
        a plotly figure
    """
    
    data_dict = json.loads(full_response)
    title=data_dict['layout']['title']
 
    chart_type = data_dict['data'][0]['type']
    if chart_type=="line":
        x_values = data_dict['data'][0]['x']
        y_values = data_dict['data'][0]['y']
       
    elif chart_type=='pie':
        x_values = data_dict['data'][0]['values']
        y_values = data_dict['data'][0]['labels']
     
    elif chart_type=='bar':
        x_values = data_dict['data'][0]['x']
        y_values = data_dict['data'][0]['y']

    fig = go.Figure()
    if chart_type == 'bar':
        fig.add_trace(go.Bar(x=x_values, y=y_values))
        fig.update_layout(title_text=title)
        return fig
    elif chart_type == 'line':
            fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines'))
            fig.update_layout(title_text=title)
            return fig
    elif chart_type == 'pie':
            fig.add_trace(go.Pie(labels=y_values,values=x_values))
            fig.update_layout(title_text=title)
            return fig
_DEFAULT_TEMPLATE ="""You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question. Unless the user specifies in the question a specific number of examples to obtain,query for at most 5 results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database.Never query for all columns from a table.Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table. Pay attention to use date('now') function to get the current date, if the question involves "today".

if the user asks for a tabular format , return the final output as an HTML table.
if the output includes multiple items , return it in a  bulletpoint format.
if the user asks about logic or reasoning or an explanation behind choosing an an opportunity or a risk , check the description field for their signals.
if the user asks about the next best action (NBA) for a client , include the links for it in this format [here](link).
Use the following format:

Question: Question here 
SQLQuery: SQL Query to run 
SQLResult: Result of the SQLQuery 
Answer: Final answer here

Only use the following tables: {table_info}

Question: {input}"""
PROMPT = PromptTemplate(
    input_variables=["input", "table_info"], template=_DEFAULT_TEMPLATE
)
def check_for_keywords(text,flag):
    if flag=="summary":
        pattern = r'\b(summary|summarize|summarization|summarize[sd]|summarizing)\b'
       
    elif flag=='visuals':
        pattern = r'\b(Plot|visualize|visualization|Draw|Graph[s]|Chart[s]|Line plot|Bar chart|Pie chart)\b'
     
    elif flag=="emails":
        pattern=r'\b(email)\b'
    elif flag=='Signals':
        pattern=r"b(signal|signal[s])\b"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return True
    else:
        return False

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
    pattern = r'Final answer\s?(Here|here:|:)?'
    full_response = re.sub(pattern, "", full_response)
    #full_response=full_response.replace('Final answer here',"")
    #full_response=full_response.replace(':'," ")
    full_response=full_response.replace("'","")
    return full_response
@st.cache_resource()
def load_db(uri):
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
    db=SQLDatabase.from_uri(st.secrets.DB_STRING)
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
        if message['role']=='user':
            icon='https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png'
        else:
            icon="https://i.ibb.co/23kfBNr/Forwardlane-chat.png"

        with st.chat_message(message["role"],avatar=icon):
            if type(message['content'])==str:
                st.markdown(message["content"],unsafe_allow_html=True)
            
            else:
                st.plotly_chart(message['content'], use_container_width=True)
def calculate_price(cb):
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}")
