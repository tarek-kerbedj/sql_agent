import itertools
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import ConversationalRetrievalChain
import streamlit as st
import os
import hashlib
from util_funcs import text_to_docs,parse_uploaded_file
from langchain.chat_models import ChatOpenAI
from langchain.llms import Bedrock
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
import boto3
client = boto3.client(
    'bedrock',
    region_name='us-east-1'
)
session = boto3.Session(
        aws_access_key_id=os.getenv('Access_key_ID'),
        aws_secret_access_key=os.getenv('Secret_access_key'),region_name='us-east-1')

llm = Bedrock(credentials_profile_name="default",
        model_id="anthropic.claude-v2"
    )
# initialize the LLM
#if vectordb not in st.session_state:
       # st.session_state.vectordb={}
if "file_name" not in st.session_state:
    st.session_state.file_name=""
#llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k",request_timeout=120)

def generate_summary(files):
    """
    this function will summarize the documents after parsing them and loading the approrpiate summarizing chain
    Parameters:
        Files(List): represents the raw uploaded files """
   
    parsed_files=[parse_uploaded_file(f) for f in files]
 
    #summary_chain = load_summarize_chain(llm=llm,chain_type="stuff")
    map_reduce = load_summarize_chain(llm=llm,
                                     chain_type='map_reduce',
                                    )
    docs=[]

    for f in parsed_files:

        summary=map_reduce.run(text_to_docs(f))
   
        st.session_state.summaries.append(summary)
    return st.session_state.summaries
                                          


@st.cache_resource
def  create_embs(parsed_files):
    """ this function creates Documents from the the text, and turns them into embeddings and finally creates a conversationalChain
           Parameters:
                parsed_files (list of lists): represents a list of the parsed documents
  
            Returns:
                    vectordb (Chroma DB): chromaDB object that contains the embeddings for all of the documents"""""
    
    # merge all the documents into a list
    merged_docs = list(itertools.chain(*parsed_files))
    # transform them into Langchain Document format
    docs=text_to_docs(merged_docs)

    # create embeddings
    embeddings = OpenAIEmbeddings()
   
    # create the vectorstore
    
    vectordb = Chroma.from_documents(docs, embeddings, collection_name="collection")

    return vectordb

def generate_answer(prompt,files):
    """ this function will handle parsing the document , turning it into embeddings and the query
         Parameters:
                parsed_files (list of lists): represents a list of the parsed documents
                prompt (str): the user query
            Returns:
                answer(str): represents the output from the LLM"""


    # if the user query is empty return a warning 
    if prompt.strip()=='':
        st.warning('user query cant be empty, Please type something in the text box')
        return
 

        # parsing the uploaded files
    try:
        parsed_files=[parse_uploaded_file(f)for f in files]

        
    except:
        st.error('Error parsing the file')

    vectordb=create_embs(parsed_files)

    
        
    # generate the answer
    pdfqa=ConversationalRetrievalChain.from_llm(llm,vectordb.as_retriever(search_kwargs={"k": 4}))
    answer = pdfqa({"question": prompt,"chat_history":st.session_state.chat_his})
    return answer['answer']
