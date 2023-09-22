import os
import json
import streamlit as st
from langchain.chat_models import ChatOpenAI
import plotly.graph_objects as go
import pandas as pd
from time import perf_counter
from plotly.graph_objs import Figure
from style import *
from llm_utilities import *
from core_funcs import  *
from util_funcs import *
from langchain.prompts.prompt import PromptTemplate
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import Bedrock
import logging
import boto3
from openai.error import RateLimitError
from opencensus.ext.azure.log_exporter import AzureLogHandler
from database_insights import handle_database_insights
from document_QA import handle_document_interaction
from signal_generation import handle_signal_generation
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
    # files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["xlsx"],key=2)
    
    # show_messages(st.session_state.messages)
    # st.session_state.uploaded_files=files
    
    # for i,f in enumerate(files):
    #     _, extension = os.path.splitext(f.name)
    #     if extension in ['.xlsx']:
    #         df = pd.read_excel(f,header=None)
    #         break
    #     if i==len(files)-1:
    #         st.error('Please upload a valid excel file')
    #         st.stop()
        
    # if prompt := st.chat_input(""):
    #     if prompt.strip()=="":
    #         st.error('Please specify a query in order to proceed')
    #         st.stop()
        
    #     st.session_state.messages.append({"role": "user", "content": prompt})
    #     with st.chat_message("user",avatar='https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png'):
    #         st.markdown(prompt)
    #     with st.chat_message("assistant",avatar='https://i.ibb.co/23kfBNr/Forwardlane-chat.png'):
    #         message_placeholder = st.empty()
    #         full_response = "" 
    #         # template = """You are a nice chatbot having a conversation with a human.

    #         # # Previous conversation:
    #         # # {chat_history}

    #         # # New human question: {question}
    #         # # Response:"""
    #         #temp = PromptTemplate.from_template(template)
    #         #if check_for_keywords(prompt,"Signals")==True:
    #         conversation=signal_generator()
    #         #conversation = LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.memory)
    #         signals='\n\n'.join(df[0])
    #         with get_openai_callback() as cb:
    #                 t1=perf_counter()
    #                 st_callback = StreamlitCallbackHandler(st.container())
    #                 full_response=conversation({"question":f'{prompt} , these are some signals for customers that should serve as an example : {signals}. makes sure that you use the same format , without any explanations . dont include the signals that i listed'})['text']
    #                 t2=perf_counter()
    #         st.markdown(full_response)
    #         total_cost,total_tokens=cb.total_cost,cb.total_tokens
    #         st.session_state['log'].append((prompt,"Signal_Generator",total_cost,total_tokens,t2-t1))
     
    #         logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Signal_Generator', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                
    #         st.session_state.messages.append({"role": "assistant", "content": full_response})
