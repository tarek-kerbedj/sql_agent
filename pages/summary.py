import streamlit as st
from langchain import OpenAI
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
#from util_funcs import parse_uploaded_file,parse_docx,parse_pdf,parse_txt
from util_funcs_summary import summary_download,summary_UI
from core_funcs import generate_summary


st.title("Summary")

if "summaries" not in st.session_state:
    st.session_state.summaries=[]
if "file_names" not in st.session_state:
    st.session_state.file_names=[]

for i in range(0,3):
    st.write('')

#option=st.radio('choose an option',("Use the same file(s)",'Upload a different file'))

#if option=="Upload a different file":
st.session_state.summaries=[]

files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt'])
# start the process only when the user inputs a file
if files !=[]:
    st.session_state.uploaded_files=files
    
    summary_UI()



# else:
#     st.session_state.summaries=[]
#     # if the user chooses to keep using the same files
#     for i in range(0,3):
#         st.write('')
#     # If there are no uploaded files saved in the session_state, raise an error
#     if st.session_state.uploaded_files==[]:
#         st.error('Please upload a file in the Q&A section to be able to use the same files option')

#     else:
#         summary_UI()
