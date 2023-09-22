import streamlit as st
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from time import perf_counter
from utils.llm_utilities import *
from utils.core_funcs import  *
from utils.util_funcs import *
logger=setup_logger()
USER_AVATAR = "https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png"
ASSISTANT_AVATAR ="https://i.ibb.co/23kfBNr/Forwardlane-chat.png"
csv_llm= ChatOpenAI(
        temperature=0.5,
        model="anthropic/claude-2",
        openai_api_key=os.getenv("openrouter"),
        openai_api_base=os.getenv("OPENROUTER_API_BASE"),headers={"HTTP-Referer": "http://localhost:8501/"},)
 
def handle_document_interaction():

    files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["pdf",'docx','txt','csv'],key=1)
 
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    if prompt := st.chat_input(""):
        if prompt.strip()=="":
            st.error('Please specify a query in order to proceed')
            st.stop()
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user",avatar=USER_AVATAR):
            st.markdown(prompt)
        with st.chat_message("assistant",avatar=ASSISTANT_AVATAR):
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
      
                            csv_conversation= LLMChain(llm=csv_llm,verbose=True,prompt=temp,memory=st.session_state.csv_memory)
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