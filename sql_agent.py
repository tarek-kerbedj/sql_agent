import os
from time import perf_counter
import streamlit as st
from langchain.chat_models import ChatOpenAI
#import plotly.graph_objects as go
#from plotly.graph_objs import Figure
#from vis_funcs import chat2plot_plot
from langchain.prompts.prompt import PromptTemplate
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from style import *
from utilities import *
os.environ["OPENAI_API_Key"]=st.secrets.OPENAI_API_KEY

# renders the title and logo
header("forward_lane_icon.png","Database Chat")

_DEFAULT_TEMPLATE ="""You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question. Unless the user specifies in the question a specific number of examples to obtain,query for at most 5 results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database. Never query for all columns from a table.Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table. Pay attention to use date('now') function to get the current date, if the question involves "today".
Wrap each column name in double quotes (") to denote them as delimited identifiers.
if the user asks for a tabular format , return the final output as an HTML table.
if the output includes multiple items , return it in a bulletpoint format.
if the user asks about an explanation or reasoning related to opportunities , query the columns related to that as well
 
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
URI=st.text_input('Insert URI')
if URI:

    db_chain=load_db(PROMPT,f"sqlite:///{URI}")
    # print out the default prompt
    st.write(db_chain.llm_chain.prompt.template)
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
                # insert visualization code later when its ready

                # try generating response if it fails return a frindly error message
                try:
                    full_response=db_chain.run(f'{prompt}')
                    full_response=clean_answer(full_response)     
                except:
                    full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
                # use markdown to be able to display html 
                st.markdown(full_response,unsafe_allow_html=True)
            
                t2=perf_counter()
                # call this function to show the price using the callback handler
                calculate_price(cb)
            
            st.session_state.chat_his.append((prompt,full_response))
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})



