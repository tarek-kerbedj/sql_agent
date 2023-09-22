import os
import streamlit as st
from langchain.chat_models import ChatOpenAI
from utils.style import *
from utils.llm_utilities import *
from utils.core_funcs import  *
from utils.util_funcs import *

from langchain.prompts.prompt import PromptTemplate
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import Bedrock
import logging
import boto3
from opencensus.ext.azure.log_exporter import AzureLogHandler
from components.database_insights import handle_database_insights
from components.document_QA import handle_document_interaction
from components.signal_generation import handle_signal_generation
#create the logging object that connects to azure logging
logger=setup_logger()
# connects to Bedrock API
#resp=connect_to_api()
resp= ChatOpenAI(
        temperature=0.5,
        model="anthropic/claude-2",
        openai_api_key=os.getenv("openrouter"),
        openai_api_base=OPENROUTER_API_BASE,headers={"HTTP-Referer": "http://localhost:8501/"},

    )

# initialize the different session state variables
load_config()
# style elements including the logo and header
header("other/images/forward_lane_icon.png","Emerge")
button_prompts=["**Client insights** \n\n query your database for insights","**Research synthesis** \n\n analyze and interact with your documents","**Signal recommendations** \n\n recommends additional signals"]
col1,col2,col3=st.columns([1,1,1])
with col1:
    button1=st.button(button_prompts[0])
with col2:
    button2=st.button(button_prompts[1])

with col3:
    button3=st.button(button_prompts[2])

login=st.text_input('Insert a username')

# admin logs
if st.session_state['log']!=[] and login in['Tarek','Roland']:
    st.download_button(
                            label="Download logs",
                            data=log_download(),
                            file_name='log.csv',
                            mime='text/csv',help="download summary in a CSV Format ",
                            )



    

    # if there are uploaded documents, let the user specify the source
if button1:
    st.session_state['source']="Database Insights"

    #documents_config(files)
    #source=st.sidebar.radio('choose a source',['Database Insights', "Document Q&A (pdf, docx, txt)",'Signal Generator (xlsx)'])
    # if there are uploaded documents, let the user specify the source
  
        
elif button2:
    st.session_state['source']="Document Q&A (pdf, docx, txt, csv - upto 3)"

elif button3:
    st.session_state['source']="Signal Generator (xlsx)"
#login process
login_config(login)

if st.session_state.source=="Database Insights":
    handle_database_insights()
  
   
elif st.session_state['source']=="Document Q&A (pdf, docx, txt, csv - upto 3)":
    handle_document_interaction()

elif st.session_state['source']=="Signal Generator (xlsx)":
    handle_signal_generation()

