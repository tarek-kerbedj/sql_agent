import json
import re
import os
from langchain.chat_models import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain
from langchain.sql_database import SQLDatabase
import streamlit as st
import yaml
from langchain.chains import LLMChain
from langchain.prompts.prompt import PromptTemplate
from plotly.graph_objs import Figure
import plotly.graph_objects as go
from langchain.llms import Bedrock
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
import boto3
OPENROUTER_BASE = "https://openrouter.ai"
OPENROUTER_API_BASE = f"{OPENROUTER_BASE}/api/v1"
os.environ["DB_STRING"]=os.getenv('DB_STRING')
#resp= Bedrock(credentials_profile_name="default",
 #     model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample":8000})
#resp=ChatOpenAI(temperature=0.5, model_name="gpt-4",request_timeout=120)
db_llm= ChatOpenAI(
        temperature=0.5,
        model_name="gpt-3.5-turbo",request_timeout=120
    )

resp= ChatOpenAI(
        temperature=0,  
        model_name="gpt-3.5-turbo",request_timeout=120
    )

@st.cache_data
def load_yaml():
    with open(f'other/prompts/prompts.yaml','r') as f:
        output = yaml.safe_load(f)
        return output
output=load_yaml()

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
    full_response=full_response.replace("'", "\"")
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
def check_for_keywords(text, flag):
    """This Function checks for certain keywords in the user prompt using regex
    Parameters:
        text (str): The input text to be checked for keywords.
        flag (str): The flag to specify which kind of keywords we are looking for.
    Returns:
        bool: True if the flag is found in the text, False otherwise.
    """
    
    patterns = {
        "summary": r'\b(summary|summarize|summarization|summarize[sd]|summarizing)\b',
        "visuals": r'\b(Plot|visualize|visualization|Draw|Graph[s]|Chart[s]|Line plot|Bar chart|Pie chart)\b',
        "emails": r'\b(email|emial|emmail|emaill)\b',
        "Signals": r'\bsignal[s]?\b|singal[s]|sginal[s]'
    }

    pattern = patterns.get(flag)
    if pattern is None:
        return False

    return bool(re.search(pattern, text, re.IGNORECASE))

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
    if not isinstance(full_response, str):
        raise ValueError("full_response must be a string")
    full_response=full_response.replace('"',"'")
    pattern = r'Final answer\s?(Here|here:|:)?'
    full_response = re.sub(pattern, "", full_response)
    
    full_response=full_response.replace("'","")
    if re.search(r'logic|reasoning',st.session_state['prompt']):
        result=resp.predict(f'here is a free text response generated {full_response} ,i want you to turn it into a bulletpoint list ,dont explain anything')

        return result
    else:
        return full_response

@st.cache_resource
def csv_handler():
    """creates a  csv handling LLM chain instance , with memory and prompt"""
    template = output['CSV HANDLING']
    temp = PromptTemplate.from_template(template)
    csv_handling = LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.csv_memory)
    return csv_handling
@st.cache_resource
def signal_generator():
    """creates a signal generator LLM chain instance , with memory and prompt
    Parameters:
        None
    Returns:
        conversation : LLMChain
            A LLMChain instance with a prompt and memory.
    """
    template=output['Signal Generator']
    temp = PromptTemplate.from_template(template)
    
    conversation = LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.memory)
    return conversation
@st.cache_resource(ttl=360)
def load_db():
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
    
    if st.session_state['user_type']!=None:
        _DEFAULT_TEMPLATE=output[st.session_state['user_type']]
    PROMPT = PromptTemplate(
    input_variables=["input", "table_info"], template=_DEFAULT_TEMPLATE)
    db=SQLDatabase.from_uri(os.getenv('DB_STRING'))
    
    db_chain = SQLDatabaseChain.from_llm(db_llm, db, verbose=True,prompt=PROMPT,return_intermediate_steps=True)
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
