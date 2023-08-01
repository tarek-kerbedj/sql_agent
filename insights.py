import os
import json
import streamlit as st
from langchain.chat_models import ChatOpenAI
import plotly.graph_objects as go
import pandas as pd
from plotly.graph_objs import Figure
from style import *
from llm_utilities import *
from core_funcs import  *
from util_funcs import *
from langchain.prompts.prompt import PromptTemplate
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain import SQLDatabase, SQLDatabaseChain


resp=ChatOpenAI(temperature=0)
if "info" not in st.session_state:
    st.session_state['info']=[]
if "source" not in st.session_state:
    st.session_state['source']="Database Insights"
if "file_names" not in st.session_state:
    st.session_state.file_names=[]
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files=[]
if "summaries" not in st.session_state:
    st.session_state.summaries=[]
os.environ["OPENAI_API_Key"]=st.secrets.OPENAI_API_KEY
# renders the title and logo

header("forward_lane_icon.png","Insights")
files=st.sidebar.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt','xlsx'])
login=st.text_input('Insert a username')
logins=pd.read_csv('logins.csv')
if (login!="") and login in logins['Name'].values:
        
        st.session_state['user']=login
        st.session_state['user_type']=logins[logins['Name']==login]['Function'].values[0]
        st.success(f"authentifaction succesful for {st.session_state['user']}")
        st.write(st.session_state['user_type'])
else:
    st.warning('Please insert an authorized username')
    st.session_state['user']=None
    st.stop()

if files !=[]:
    if "chat_his" not in st.session_state:
        st.session_state.chat_his=[]
    if "messages" not in st.session_state:
        st.session_state['messages']=[]
    st.session_state.uploaded_files=files
    source=st.sidebar.radio('choose a source',['Database Insights','Document Q&A','Signal Generator'])
    if source:
        st.session_state['source']=source


URI=st.text_input('Insert URI',value="master_mock_up.db")
if URI:
    if st.session_state.source=="Database Insights":
        db_chain=load_db(f"sqlite:///{URI}")
        # print out the default prompt
        #st.write(db_chain.llm_chain.prompt.template)
        # save messages and chat history session state
     
        if "messages" not in st.session_state:
            st.session_state['messages']=[]
            st.session_state.messages.append({"role": "assistant", "content": "Hello, how  may I help you today ?"})
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
                
                with get_openai_callback() as cb:
                    st_callback = StreamlitCallbackHandler(st.container())
        
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
                        intermediate=db_chain(f'{prompt}')
                        full_response=intermediate["intermediate_steps"]
        
                        intermediate=(intermediate["intermediate_steps"][0]['input'])
        
                        full_response=resp.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example for a bar chart {example}")
                
                        full_response=full_response.replace("'", "\"")
                    
                        full_response=preprocess_visuals(full_response)
                        st.plotly_chart(full_response, use_container_width=True)
                    else:
                        if check_for_keywords(prompt,"emails"):
                            infos='\n'.join(st.session_state.info[-2:])
                            full_response=resp.predict(f"given this information about a client {infos} generate me a concise email that doesnt exceed 125 words .dont include any numerical scores. dont forget to include the links in this format [here](link)")
                            st.markdown(full_response)
                      

                        else:

                            try:
                                    full_response=db_chain(f'{prompt}')['result']
                                    full_response=clean_answer(full_response)
                                    st.session_state['info'].append(full_response)
                                    st.markdown(full_response,unsafe_allow_html=True)
                            except:
                                full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
                    
                    # use markdown to be able to display html 
                                st.markdown(full_response,unsafe_allow_html=True)
            
                    # call this function to show the price using the callback handler
                    calculate_price(cb)
                
        
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    elif st.session_state['source']=="Document Q&A":
        show_messages(st.session_state.messages)
        st.session_state.uploaded_files=files
        if prompt := st.chat_input("What would you like to know about this document?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user",avatar="https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png"):
                st.markdown(prompt)
            with st.chat_message("assistant",avatar="https://i.ibb.co/23kfBNr/Forwardlane-chat.png"):
                message_placeholder = st.empty()
                full_response = "" 
                if check_for_keywords(prompt,"summary")==False:

                    full_response=generate_answer(prompt,st.session_state.uploaded_files)
                    st.session_state.chat_his.append((prompt,full_response))
                    st.markdown(full_response)
           
                else:
                    if (st.session_state.uploaded_files)==[]:
                        full_response=('Please make sure to upload a document before proceeding')
                        st.write(full_response)
                    else:
            
                        st.session_state.summaries=[]
                        st.session_state.file_names=[]
                        for f in st.session_state.uploaded_files:
                            st.write("- "+f.name)
                            st.session_state.file_names.append(f.name.split('.')[0])
        
                        full_response="\n\n\n\n".join(generate_summary(st.session_state.uploaded_files))
                        st.markdown(full_response,unsafe_allow_html=True)
                        st.write(len(st.session_state.uploaded_files))
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
        df = pd.read_excel(st.session_state['uploaded_files'][0],header=None)
        if prompt := st.chat_input("What would you like to know about this document?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user",avatar='https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png'):
                st.markdown(prompt)
            with st.chat_message("assistant",avatar='https://i.ibb.co/23kfBNr/Forwardlane-chat.png'):
                message_placeholder = st.empty()
                full_response = "" 
                if check_for_keywords(prompt,"Signals")==False:
                    signals='\n\n'.join(df[0])
                    full_response=response= openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=[{"role": "system", "content": ""},
                    {"role": "user", "content": f"{prompt},generate 10 more signals,these are some signals for customers {signals}. makes sure that you use the same format , without any explanations"}])['choices'][0]['message']['content']

                    #full_response=resp_predict(f'{prompt} ,these are some signals for customers {signals}. makes sure that you use the same format , without any explanations')
                    #full_response=resp.predict(f'You are an asset manager and these are some signals for customers {signals}. Can you generate a few more in the same format , without any explanations')
                    st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
