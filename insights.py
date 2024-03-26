import os
import streamlit as st
from langchain.chat_models import ChatOpenAI
from utils.style import *
from utils.llm_utilities import *
from utils.core_funcs import *
from utils.util_funcs import *
from components.database_insights import handle_database_insights
from components.document_QA import handle_document_interaction
from components.signal_generation import handle_signal_generation
from langchain.llms import Bedrock
import logging
import boto3
from opencensus.ext.azure.log_exporter import AzureLogHandler

# create the logging object that connects to azure logging
logger = setup_logger()

# initialize the different session state variables
load_config()
# style elements including the logo and header
logo_path = os.path.join('other', 'images', 'logo.png')
header(logo_path, "Emerge")
button_prompts = [
    "**Client insights** \n\n query your database for insights",
    "**Research synthesis** \n\n analyze and interact with your documents",
    "**Signal recommendations** \n\n recommends additional signals",
]
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    client_insights_button = st.button(button_prompts[0])
with col2:
    research_synthesis_button = st.button(button_prompts[1])
with col3:
    signal_generation_button = st.button(button_prompts[2])

login = st.text_input("Insert a username")

# admin logs
if st.session_state["log"] != [] and login in ["Tarek", "Roland"]:
    st.download_button(
        label="Download logs",
        data=log_download(),
        file_name="log.csv",
        mime="text/csv",
        help="download summary in a CSV Format ",
    )

    # if there are uploaded documents, let the user specify the source
if client_insights_button:
    st.session_state["source"] = "Database Insights"

    # documents_config(files)
    # source=st.sidebar.radio('choose a source',['Database Insights', "Document Q&A (pdf, docx, txt)",'Signal Generator (xlsx)'])
    # if there are uploaded documents, let the user specify the source


elif research_synthesis_button:
    st.session_state["source"] = "Document Q&A (pdf, docx, txt, csv - upto 3)"

elif signal_generation_button:
    st.session_state["source"] = "Signal Generator (xlsx)"
# login process
login_config(login)

if st.session_state.source == "Database Insights":
    handle_database_insights()


elif st.session_state["source"] == "Document Q&A (pdf, docx, txt, csv - upto 3)":
    handle_document_interaction()

elif st.session_state["source"] == "Signal Generator (xlsx)":
    handle_signal_generation()
