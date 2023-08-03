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

resp=ChatOpenAI(temperature=0)

load_config()

os.environ["OPENAI_API_Key"]=st.secrets.OPENAI_API_KEY
# renders the title and logo

header("forward_lane_icon.png","Insights")
files=st.sidebar.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt','xlsx'])
login=st.text_input('Insert a username')

if st.session_state['log']!=[] and login in['Tarek','Roland']:
    st.download_button(
                            label="Download logs",
                            data=log_download(),
                            file_name='log.csv',
                            mime='text/csv',help="download summary in a CSV Format ",
                            )


if files !=[]:
    documents_config(files)
    source=st.sidebar.radio('choose a source',['Database Insights','Document Q&A','Signal Generator'])
    # if there are uploaded documents , let the user specify the source
    if source:
        st.session_state['source']=source
else:
    # if there are no files uploaded , default to the database
    st.session_state['source']="Database Insights"

login_config(login)

if st.session_state.source=="Database Insights":
    db_chain=load_db()
    # print out the default prompt
    #st.write(db_chain.llm_chain.prompt.template)
    # save messages and chat history session state

    
    show_messages(st.session_state.messages)   
    
    if prompt := st.chat_input("How many clients are there?"):
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
                    example={'data': [
            {
                'x': [
                    "giraffes",
                    "orangutans",
                    "monkeys"
                ],
                'y': [
                    20,
                    14,
                    23
                ],
                'type': 'bar'
            }
        ],  'layout': {
            'title': 'Plot Title'
        }
    }               
                    with get_openai_callback() as cb:
                        st_callback = StreamlitCallbackHandler(st.container())
                        t1=perf_counter()
                        intermediate=db_chain(f'{prompt}')
                        full_response=intermediate["intermediate_steps"]
        
                        intermediate=(intermediate["intermediate_steps"][0]['input'])
        
                        full_response=resp.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example for a bar chart {example}")
                
                        full_response=full_response.replace("'", "\"")
                    
                        full_response=preprocess_visuals(full_response)
                        t2=perf_counter()
                    total_cost,total_tokens=calculate_price(cb)
                    st.session_state['log'].append((prompt,"Visualization",total_cost,total_tokens,t2-t1))
                    st.plotly_chart(full_response, use_container_width=True)
            else:

                    if check_for_keywords(prompt,"emails"):
                        with get_openai_callback() as cb:
                            st_callback = StreamlitCallbackHandler(st.container())
                            t1=perf_counter()
                            infos='\n'.join(st.session_state.info[-2:])
                            full_response=resp.predict(f"given this information about a client {infos} generate me a concise email that doesnt exceed 125 words .dont include any numerical scores. dont forget to include the links in this format [here](link)")
                            t2=perf_counter()
                        total_cost,total_tokens=calculate_price(cb)
                        st.session_state['log'].append((prompt,"Email",total_cost,total_tokens,t2-t1))
                        st.markdown(full_response)
                

                    else:

                        try:
                            with get_openai_callback() as cb:
                                st_callback = StreamlitCallbackHandler(st.container())
                                t1=perf_counter()
                                full_response=db_chain(f'{prompt}')['result']
                                full_response=clean_answer(full_response)
                                t2=perf_counter()
                            total_cost,total_tokens=calculate_price(cb)
                            st.session_state['log'].append((prompt,"DB CALL",total_cost,total_tokens,t2-t1))
                            st.session_state['info'].append(full_response)
                            st.markdown(full_response,unsafe_allow_html=True)
                        except:
                            full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
                
                # use markdown to be able to display html 
                            st.markdown(full_response,unsafe_allow_html=True)
                
    
        st.session_state.messages.append({"role": "assistant", "content": full_response})
elif st.session_state['source']=="Document Q&A":
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    if prompt := st.chat_input("What would you like to know about this document?"):
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
                total_cost,total_tokens=calculate_price(cb)
                st.session_state['log'].append((prompt,"Document Q&A",total_cost,total_tokens,t2-t1))
                    
                st.session_state.chat_his.append((prompt,full_response))
                st.markdown(full_response)
    
            else:
                if (st.session_state.uploaded_files)==[]:
                    full_response=('Please make sure to upload a document before proceeding')
                    st.write(full_response)
                else:
                    
                    st.session_state.summaries=[]
                    st.session_state.file_names=[]
                    st.write('Summarizing the file(s) below...')
                    for f in st.session_state.uploaded_files:
                        st.write("- "+f.name)
                        _, extension = os.path.splitext(f.name)
                        if extension not in ['.pdf','.docx',".txt"]:
                            st.error('Please upload a valid document , currently the supported documents are : PDFs, Docx and text files')
                            st.stop()
                        st.session_state.file_names.append(f.name.split('.')[0])

                    full_response="\n\n\n\n".join(generate_summary(st.session_state.uploaded_files))
                    st.markdown(full_response,unsafe_allow_html=True)
    
                    if len(st.session_state.uploaded_files)>1:                
                        st.download_button(
                        label="Download summary",
                        data=summary_download(),
                        file_name='summary.zip',
                        mime='application/zip',help="download summary/summaries in a PDF Format ",
                        )
                    elif len(st.session_state.uploaded_files)==1:
            
                        st.download_button(
                        label="Download summary",
                        data=summary_download(),
                        file_name='summary.pdf',
                        mime='application/pdf',help="download summary in a PDF Format ",
                        )
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
elif st.session_state['source']=="Signal Generator":
    
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
        
    if prompt := st.chat_input("you are an asset manager , help me generate similair signals"):
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
            if check_for_keywords(prompt,"Signals")==False:
                conversation = LLMChain(
                        llm=resp,
                        verbose=True,prompt=temp,
                        memory=st.session_state.memory
                    )
                signals='\n\n'.join(df[0])
                with get_openai_callback() as cb:
                        t1=perf_counter()
                        st_callback = StreamlitCallbackHandler(st.container())
                        full_response=conversation({"question":f'{prompt} ,these are some signals for customers {signals}. makes sure that you use the same format , without any explanations'})['text']
                #full_response=resp.predict(f'{prompt} ,these are some signals for customers {signals}. makes sure that you use the same format , without any explanations')
                #full_response=resp.predict(f'You are an asset manager and these are some signals for customers {signals}. Can you generate a few more in the same format , without any explanations')
                        t2=perf_counter()
                st.markdown(full_response)
                total_cost,total_tokens=calculate_price(cb)
                st.session_state['log'].append((prompt,"Signal_Generator",total_cost,total_tokens,t2-t1))
            st.session_state.messages.append({"role": "assistant", "content": full_response})
