import os
import streamlit as st
import pandas as pd
from time import perf_counter
from utils.llm_utilities import *
from utils.core_funcs import  *
from utils.util_funcs import *
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
logger=setup_logger()
USER_AVATAR = "https://creazilla-store.fra1.digitaloceanspaces.com/icons/3257916/gender-neutral-user-icon-md.png"
ASSISTANT_AVATAR ="https://i.ibb.co/23kfBNr/Forwardlane-chat.png"
def handle_signal_generation():
    files=st.file_uploader("Choose a file",accept_multiple_files=True,type=["xlsx"],key=2)
    
    show_messages(st.session_state.messages)
    st.session_state.uploaded_files=files
    for i, f in enumerate(files):
        _, extension = os.path.splitext(f.name)
        if extension in ['.xlsx']:
            signals_df = pd.read_excel(f, header=None)
            break
        if i == len(files) - 1:
            st.error('Please upload a valid excel file')
            st.stop()
        
    if prompt := st.chat_input(""):
        if prompt.strip() == "":
            st.error('Please specify a query in order to proceed')
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            message_placeholder = st.empty()
            full_response = "" 

            conversation=signal_generator()
 
            signals='\n\n'.join(signals_df[0])
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