import os
import json
from time import perf_counter
import pandas as pd
import streamlit as st

from langchain.agents import create_pandas_dataframe_agent
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from vis_funcs import *
from style import *
from utilities import *
from core_funcs import  generate_summary
from util_funcs_summary import summary_download
from langchain.prompts.prompt import PromptTemplate
from langchain.agents.agent_types import AgentType
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from langchain.sql_database import SQLDatabase

if "file_names" not in st.session_state:
    st.session_state.file_names=[]
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files=[]
if "summaries" not in st.session_state:
    st.session_state.summaries=[]
os.environ["OPENAI_API_Key"]=st.secrets.OPENAI_API_KEY
# renders the title and logo
header("forward_lane_icon.png","Insights")
files=st.sidebar.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt'])
if files !=[]:
    st.session_state.uploaded_files=files
#if the user asks about an explanation or reasoning related to opportunities , query the columns related to that as well
#dont use the client_breakdown table unless the user asks about a certain client.

# Wrap each column name in double quotes (") to denote them as delimited identifiers.
_DEFAULT_TEMPLATE ="""You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question. Unless the user specifies in the question a specific number of examples to obtain,query for at most 5 results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database.Never query for all columns from a table.Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table. Pay attention to use date('now') function to get the current date, if the question involves "today".

if the user asks for a tabular format , return the final output as an HTML table.
if the output includes multiple items , return it in a  bulletpoint format.
if the user asks about reasoning or an explanation behind choosing an an opportunity or a risk , check the description field for his signals
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

URI=st.text_input('Insert URI',value="master_mock_up.db")
if URI:

    db_chain=load_db(f"sqlite:///{URI}")
    # print out the default prompt
    #st.write(db_chain.llm_chain.prompt.template)
    # save messages and chat history session state
    if "chat_his" not in st.session_state:
        st.session_state.chat_his=[]
    if "messages" not in st.session_state:
        st.session_state['messages']=[]

    show_messages(st.session_state.messages)
        
    
    if prompt := st.chat_input("What would you like to know about this document?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            with get_openai_callback() as cb:
                st_callback = StreamlitCallbackHandler(st.container())
                t1=perf_counter()
                resp=ChatOpenAI(temperature=0)
                if check_for_visuals(prompt)==True:
                    print('PLOT')
                    #choice=resp.predict(f"is the user query asking for a data visualization task ?,some examples of data visualization tasks are : using verbs like show ,visualize and plot \n  answer with either yes or a no , here is the query :{prompt}")
                    #if choice.lower() in ["yes","yes."]:
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
                    #st.write(full_response)
                    #st.write(full_response[3])
                    #st.write(intermediate["intermediate_steps"][2])


                    full_response=resp.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example for a bar chart {example}")
            
                    full_response=full_response.replace("'", "\"")
                
                    full_response=preprocess_visuals(full_response)
                    st.plotly_chart(full_response, use_container_width=True)
                else:
                    if check_for_summary(prompt)==False:
                        try:
                            print('ok')
                            full_response=db_chain(f'{prompt}')['result']
                            full_response=clean_answer(full_response)
                            st.markdown(full_response,unsafe_allow_html=True)
                        except:
                            full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
                    else:
                        #check if list is not empty
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

                # use markdown to be able to display html 
                #st.markdown(full_response,unsafe_allow_html=True)
            
                t2=perf_counter()
                # call this function to show the price using the callback handler
                calculate_price(cb)
            
            st.session_state.chat_his.append((prompt,full_response))
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})



