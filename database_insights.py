import streamlit as st
from langchain.callbacks import get_openai_callback,StreamlitCallbackHandler
from time import perf_counter
from llm_utilities import *
from core_funcs import  *
from util_funcs import *

logger=setup_logger()
misc_llm= ChatOpenAI(
        temperature=0.5,
        model="anthropic/claude-2",
        openai_api_key=os.getenv("openrouter"),
        openai_api_base=OPENROUTER_API_BASE,headers={"HTTP-Referer": "http://localhost:8501/"},

    )
def handle_database_insights():

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
        
                        full_response=misc_llm.predict(f"given this answer from an SQL query {intermediate},generate and return the appropriate plotly JSON schema without any explainations or elaborations ,  here is an example for a bar chart {st.session_state.example}")
                
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
                            full_response=misc_llm.predict(f"given this information about a client {infos} generate me a concise email that doesnt exceed 125 words .dont include any numerical scores. dont forget to include the links in this format [here](link)")
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