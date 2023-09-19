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
from openai.error import RateLimitError
from opencensus.ext.azure.log_exporter import AzureLogHandler
#create the logging object that connects to azure logging
logger=setup_logger()
# connects to Bedrock API
#resp=connect_to_api()
resp=ChatOpenAI(temperature=0.5, model_name="gpt-4",request_timeout=120)
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
    #initiate the database sqlchain
    db_chain=load_db()
        
    show_messages(st.session_state.messages)   
    # input check
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
elif st.session_state['source']=="Document Q&A (pdf, docx, txt, csv - upto 3)":
    files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt','csv'],key=1)
    documents_config(files)
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
            template = """You are a nice chatbot with access to csv files, having a conversation with a human and helping him out analyze and understand these documents.

            Previous conversation:
            {chat_history}

            New human question: {question}
            Response:"""
            temp = PromptTemplate.from_template(template) 
            if check_for_keywords(prompt,"summary")==False:
                if check_csv_files(st.session_state.uploaded_files)==True:
                    if len(st.session_state.uploaded_files)>0:
                        try:

                            dataframes=[parse_csv(f) for f in st.session_state.uploaded_files]
                        except:
                            st.error("Error parsing the csv files , please make sure to upload a valid csv file")
                        try:
                            csv_conversation= LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.csv_memory)
                            full_response=csv_conversation({"question":f' given this list of CSVs  \n :{dataframes[0:min(3,len(st.session_state.uploaded_files))]} ,{prompt} '})['text']
                            st.markdown(full_response)
                            st.session_state.chat_his.append((prompt,full_response))
                        except RateLimitError as e:
                            st.error('OpenAI rate limit reached,this is a limitation set by OpenAI itself ,please try again later')
                       
                else:

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
                    st.write(f"response time : **{t2-t1:.2f}** seconds")
                    st.write("**Summary**:")
                    
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
    files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["xlsx"],key=2)
    
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    
    for i,f in enumerate(files):
        _, extension = os.path.splitext(f.name)
        if extension in ['.xlsx']:
            df = pd.read_excel(f,header=None)
            break
        if i==len(files)-1:
            st.error('Please upload a valid excel file')
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
            # template = """You are a nice chatbot having a conversation with a human.

            # # Previous conversation:
            # # {chat_history}

            # # New human question: {question}
            # # Response:"""
            #temp = PromptTemplate.from_template(template)
            #if check_for_keywords(prompt,"Signals")==True:
            conversation=signal_generator()
            #conversation = LLMChain(llm=resp,verbose=True,prompt=temp,memory=st.session_state.memory)
            signals='\n\n'.join(df[0])
            with get_openai_callback() as cb:
                    t1=perf_counter()
                    st_callback = StreamlitCallbackHandler(st.container())
                    full_response=conversation({"question":f'{prompt} , these are some signals for customers that should serve as an example : {signals}. makes sure that you use the same format , without any explanations . dont include the signals that i listed'})['text']
                    t2=perf_counter()
            st.markdown(full_response)
            total_cost,total_tokens=cb.total_cost,cb.total_tokens
            st.session_state['log'].append((prompt,"Signal_Generator",total_cost,total_tokens,t2-t1))
     
            logger.info('Task completed', extra={"custom_dimensions":{'TaskType': 'Signal_Generator', 'Price': f'${total_cost:.3f}','Tokens': f'{total_tokens:.3f}','Time': f'{t2-t1:.3f}'}})
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
