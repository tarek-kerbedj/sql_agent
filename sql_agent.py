import os
import json
from time import perf_counter
import pandas as pd
import streamlit as st

from langchain.agents import create_pandas_dataframe_agent
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

#import plotly.graph_objects as go
#from plotly.graph_objs import Figure
#from vis_funcs import chat2plot_plot
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.agents.agent_types import AgentType
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from langchain.sql_database import SQLDatabase
import base64
from pathlib import Path
from style import load_bootstrap



load_bootstrap()


col1,col2,col3=st.columns([1,1,1])





def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
      img_to_bytes(img_path)
    )
    return img_html
with col2:
    #st.image('forward_lane_icon.png')
    st.markdown(img_to_html('forward_lane_icon.png'), unsafe_allow_html=True)
st.title('Database Chat')

os.environ["OPENAI_API_Key"]=st.secrets.OPENAI_API_KEY
_DEFAULT_TEMPLATE ="""You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question. Unless the user specifies in the question a specific number of examples to obtain, query for at most 5 results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database. Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers. Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table. Pay attention to use date('now') function to get the current date, if the question involves "today".
if the user asks for a tabular format , return the final output as an HTML table
if the output includes a list of items , return it as an html list
Use the following format:

Question: Question here SQLQuery: SQL Query to run SQLResult: Result of the SQLQuery Answer: Final answer here

Only use the following tables: {table_info}

Question: {input}"""
PROMPT = PromptTemplate(
    input_variables=["input", "table_info"], template=_DEFAULT_TEMPLATE
)
@st.cache_resource
def load_db():
    db=SQLDatabase.from_uri("sqlite:///master_mock_up.db")
    db_chain = SQLDatabaseChain.from_llm(ChatOpenAI(temperature=0), db, verbose=True,prompt=PROMPT)
    return db_chain
db_chain=load_db()

    






#st.write(db_chain.llm_chain.prompt.template)
if "chat_his" not in st.session_state:
    st.session_state.chat_his=[]
if "messages" not in st.session_state:
    st.session_state['messages']=[]



#df = pd.read_csv("dataset_100000.csv")

# this code writes down the messages in the chat history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        if type(message['content'])==str:
            st.markdown(message["content"],unsafe_allow_html=True)
        
        else:
            pass
        # else:
        #     if isinstance(message['content'].figure, Figure):
        #         st.plotly_chart(message['content'].figure, use_container_width=True)
        #     else:
        #         st.vega_lite_chart(df, message['content'].config, use_container_width=True)


     
   
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
            # choice=resp.predict(f"is the user query asking for a data visualization task ?,some examples of data visualization tasks are : using verbs like show ,visualize and plot \n  answer with either yes or a no , here is the query :{prompt}")
            # if choice.lower() in ["yes","yes."]:
#                 example={'data': [
#         {
#             'x': [
#                 "giraffes",
#                 "orangutans",
#                 "monkeys"
#             ],
#             'y': [
#                 20,
#                 14,
#                 23
#             ],
#             'type': 'bar'
#         }
#     ]
# }
                #intermediate=db_chain(f'{prompt}')
                #full_response=intermediate["intermediate_steps"]
                #st.write(intermediate["intermediate_steps"][2])


                # full_response=resp.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example {example}")
                # full_response=full_response.replace("'", "\"")
                # data_dict = json.loads(full_response)

                # x_values = data_dict['data'][0]['x']
                # y_values = data_dict['data'][0]['y']
                # chart_type = data_dict['data'][0]['type']
                # st.write(full_response)
                #full_response=chat2plot_plot(df,prompt)
                # fig = go.Figure()
                # # if chart_type == 'bar':
                # #      fig.add_trace(go.Bar(x=x_values, y=y_values))
                # #      st.plotly_chart(fig ,use_container_width=True)
                # # elif chart_type == 'line':
                # #      fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines'))
                # #      st.plotly_chart(fig, use_container_width=True)
                # if isinstance(full_response.figure, Figure):
                #       st.plotly_chart(full_response.figure, use_container_width=True)
                # else:
                #       st.vega_lite_chart(df, full_response.config, use_container_width=True)  
                
              
                #st.write(full_response)
                
                # full_response=chat2plot_plot(df,prompt)
                # 
   
            try:
                #rail_guard=ChatOpenAI(temperature=0)
                #rail_guard.predict(f' {prompt}')

                full_response=db_chain.run(f'{prompt}').replace('Final answer here:',"")
           
            except:
                full_response="Sorry this question is not related to the data ,could you please ask a question specific to the database\n "
            st.markdown(full_response,unsafe_allow_html=True)
      
            t2=perf_counter()
            print(f"total time taken: {t2-t1}")
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}")
    
       
        st.session_state.chat_his.append((prompt,full_response))
       
   
    st.session_state.messages.append({"role": "assistant", "content": full_response})



