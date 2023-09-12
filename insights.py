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
from langchain import SQLDatabase, SQLDatabaseChain
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import Bedrock
import logging
import boto3
from opencensus.ext.azure.log_exporter import AzureLogHandler
logger=setup_logger()

# @st.cache_resource(show_spinner=False)
# def connect_to_api():

#     client = boto3.client(
#         'bedrock',
#         region_name='us-east-1'
#     )
#     session = boto3.Session(
#             aws_access_key_id=os.getenv('Access_key_ID'),
#             aws_secret_access_key=os.getenv('Secret_access_key'),region_name='us-east-1'
#         )
#     #os.environ["OPENAI_API_Key"]=os.getenv('OPENAI_API_KEY')
#     #resp=ChatOpenAI(temperature=0)
#     resp = Bedrock(credentials_profile_name="default",
#             model_id="anthropic.claude-v2",model_kwargs={"max_tokens_to_sample":8000}
#         )
#     return resp
resp=connect_to_api()


# file_path = "/home/test.txt"
# with open(file_path, 'w') as file:
#     file.write("Hello, World!")
# isFile = os.path.isfile(file_path)
# if isFile:
#     st.write('File does exist')
# else:
#     st.write('File does not exist')
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# logger.addHandler(AzureLogHandler(connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')))

load_config()
header("forward_lane_icon.png","Insights")
files=st.sidebar.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt','xlsx'])
login=st.text_input('Insert a username')
# admin logs
if st.session_state['log']!=[] and login in['Tarek','Roland']:
    st.download_button(
                            label="Download logs",
                            data=log_download(),
                            file_name='log.csv',
                            mime='text/csv',help="download summary in a CSV Format ",
                            )


if files !=[]:
    documents_config(files)
    source=st.sidebar.radio('choose a source',['Database Insights', "Document Q&A (pdf, docx, txt)",'Signal Generator (xlsx)'])
    # if there are uploaded documents, let the user specify the source
    if source:
        st.session_state['source']=source
else:
    # if there are no files uploaded , default to the database
    st.session_state['source']="Database Insights"
#login process
login_config(login)

if st.session_state.source=="Database Insights":
    db_chain=load_db()
        
    show_messages(st.session_state.messages)   
    
    if prompt := st.chat_input(""):
        if prompt.strip()=="":
            st.error('Please specify a query in order to proceed')
            st.stop()
        st.session_state['prompt']=prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user",avatar='https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png'):
            st.markdown(prompt)
        with st.chat_message("assistant",avatar='https://i.ibb.co/23kfBNr/Forwardlane-chat.png'):
            message_placeholder = st.empty()
            full_response = ""
            
            if check_for_keywords(prompt,"visuals"):       
                    # context manager to calculate number of tokens / cost
                    with get_openai_callback() as cb:
                        st_callback = StreamlitCallbackHandler(st.container())
                        t1=perf_counter()
                        intermediate=db_chain(f'{prompt}')
                        full_response=intermediate["intermediate_steps"]
        
                        intermediate=(intermediate["intermediate_steps"][0]['input'])
        
                        full_response=resp.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example for a bar chart {st.session_state.example}")
                
                        full_response=preprocess_visuals(full_response)
                        t2=perf_counter()
                    total_cost,total_tokens=cb.total_cost,cb.total_tokens
                    
                    st.session_state['log'].append((prompt,"Visualization",total_cost,total_tokens,t2-t1))
              
              
                    logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Visualization', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})

              
        
                    if (t2-t1)>10:
                        logging.warning('Visualization took too long')
                    st.plotly_chart(full_response, use_container_width=True)
            else:

                    if check_for_keywords(prompt,"emails"):
                        # context manager to calculate number of tokens / cost
                        with get_openai_callback() as cb:
                            st_callback = StreamlitCallbackHandler(st.container())
                            t1=perf_counter()
                            infos='\n'.join(st.session_state.info[-2:])
                            full_response=resp.predict(f"given this information about a client {infos} generate me a concise email that doesnt exceed 125 words .dont include any numerical scores. dont forget to include the links in this format [here](link)")
                            t2=perf_counter()

                        total_cost,total_tokens=cb.total_cost,cb.total_tokens
                        st.session_state['log'].append((prompt,"Email",total_cost,total_tokens,t2-t1))           
                        logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Email', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                        st.markdown(full_response)
                

                    else:

                        try:
                            # context manager to calculate number of tokens / cost
                            with get_openai_callback() as cb:
                                st_callback = StreamlitCallbackHandler(st.container())
                                t1=perf_counter()
                                full_response=db_chain(f'{prompt}')['result']
                                full_response=clean_answer(full_response)
                                t2=perf_counter()
                            total_cost,total_tokens=cb.total_cost,cb.total_tokens
                            st.session_state['log'].append((prompt,"DB_CALL",total_cost,total_tokens,t2-t1))
                        
                            logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'DB_QUERY', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                            st.session_state['info'].append(full_response)
                            st.markdown(full_response,unsafe_allow_html=True)
                        except:
                            full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
                
                # use markdown to be able to display html 
                            st.markdown(full_response,unsafe_allow_html=True)
                
    
        st.session_state.messages.append({"role": "assistant", "content": full_response})
elif st.session_state['source']=="Document Q&A (pdf, docx, txt)":
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    if prompt := st.chat_input(""):
        if prompt.strip()=="":
            st.error('Please specify a query in order to proceed')
            st.stop()
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user",avatar="https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png"):
            st.markdown(prompt)
        with st.chat_message("assistant",avatar="https://i.ibb.co/23kfBNr/Forwardlane-chat.png"):
            message_placeholder = st.empty()
            full_response = "" 
            if check_for_keywords(prompt,"summary")==False:
                with get_openai_callback() as cb:
                        t1=perf_counter()
                        st_callback = StreamlitCallbackHandler(st.container())
                        full_response=generate_answer(prompt,st.session_state.uploaded_files)
                        t2=perf_counter()
                total_cost,total_tokens=cb.total_cost,cb.total_tokens
                st.session_state['log'].append((prompt,"Document Q&A",total_cost,total_tokens,t2-t1))
                logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Document_Q&A', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                st.session_state.chat_his.append((prompt,full_response))
                st.markdown(full_response)
    
            else:
                
                if (st.session_state.uploaded_files)==[]:
                    full_response=('Please make sure to upload a document before proceeding')
                    st.write(full_response)
                else:
                    
                    st.session_state.summaries=[]
                    st.session_state.file_names=[]
                    files_to_summarize=[]
                    for f in st.session_state.uploaded_files:
                        fname, extension = os.path.splitext(f.name)
                    
                        if fname in prompt:
                            files_to_summarize.append(f)
                            st.write(fname)
               
                    st.write('Summarizing the file(s) below...')
                    if files_to_summarize==[]:
                        files_to_summarize=st.session_state.uploaded_files
                    else:
                        pass
                    for f in files_to_summarize:
                        st.write(f"- Filename:  **{f.name}**")
                        _, extension = os.path.splitext(f.name)
                        if extension not in ['.pdf','.docx',".txt"]:
                            st.error('Please upload a valid document , currently the supported documents are : PDFs, Word documents(DocX) and text files')
                            st.stop()
                        st.session_state.file_names.append(f.name.split('.')[0])
                    t1=perf_counter()
                    full_response="\n\n\n\n **Summary**:".join(generate_summary(files_to_summarize))
                    t2=perf_counter()
                    st.write(f"response time : {t2-t1:.2f} seconds")
                    #st.write("**Summary**:")
                    full_response="**Summary**:"+full_response
                    st.markdown(full_response,unsafe_allow_html=True)
                
                    if len(files_to_summarize)>1:                
                        st.download_button(
                        label="Download summary",
                        data=summary_download(),
                        file_name='summary.zip',
                        mime='application/zip',help="download summary/summaries in a PDF Format ",
                        )
                    elif len(files_to_summarize)==1:
            
                        st.download_button(
                        label="Download summary",
                        data=summary_download(),
                        file_name='summary.pdf',
                        mime='application/pdf',help="download summary in a PDF Format ",
                        )
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
elif st.session_state['source']=="Signal Generator (xlsx)":
    
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    _, extension = os.path.splitext(st.session_state['uploaded_files'][0].name)
    if extension not in ['.xlsx']:
        st.error('Please upload a valid excel file')
        st.stop()
    try:

        df = pd.read_excel(st.session_state['uploaded_files'][0],header=None)
    except:
        st.error('Error parsing the excel file')
        st.stop()
        
    if prompt := st.chat_input(""):
        if prompt.strip()=="":
            st.error('Please specify a query in order to proceed')
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user",avatar='https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png'):
            st.markdown(prompt)
        with st.chat_message("assistant",avatar='https://i.ibb.co/23kfBNr/Forwardlane-chat.png'):
            message_placeholder = st.empty()
            full_response = "" 
            template = """You are a nice chatbot having a conversation with a human.

            Previous conversation:
            {chat_history}

            New human question: {question}
            Response:"""
            temp = PromptTemplate.from_template(template)
            if check_for_keywords(prompt,"Signals")==True:
                conversation = LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.memory)
                signals='\n\n'.join(df[0])
                with get_openai_callback() as cb:
                        t1=perf_counter()
                        st_callback = StreamlitCallbackHandler(st.container())
                        full_response=conversation({"question":f'{prompt} , these are some signals for customers that should serve as an example : {signals}. makes sure that you use the same format , without any explanations . dont include the signals that i listed'})['text']
                #full_response=resp.predict(f'You are an asset manager and these are some signals for customers {signals}. Can you generate a few more in the same format , without any explanations')
                        t2=perf_counter()
                st.markdown(full_response)
                total_cost,total_tokens=cb.total_cost,cb.total_tokens
                st.session_state['log'].append((prompt,"Signal_Generator",total_cost,total_tokens,t2-t1))
     
                logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Signal_Generator', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
