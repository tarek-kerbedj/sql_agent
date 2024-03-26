import re
import io
import os
import zipfile
import docx2txt
from pypdf import PdfReader
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from fpdf import FPDF
import streamlit as st
import pandas as pd
logins = pd.read_csv('logins.csv')

def documents_config(files: list) -> None:
    """ this function restarts the chat history  and the uploaded files in the session state"""
    st.session_state.chat_his = []

    st.session_state.uploaded_files = files

def login_config(login: str) -> None:
    if (login != "") and login in logins['Name'].values:

        st.session_state['user'] = login
        st.session_state['user_type'] = logins[logins['Name'] == login]['Function'].values[0]
        st.success(f"Successful authentication for {st.session_state['user']}")
    else:
        st.warning('Please insert an authorized username')
        st.session_state['user'] = None
        st.stop()

def load_config() -> None:
    """this function initializes session states for the different variables that are used in the app such as the log, source, etc...
    parameters:
        None
    Returns:
        None"""
    if "log" not in st.session_state:
        st.session_state['log'] = []
        st.session_state['log'].append(('Prompt', 'Operation', 'Cost($)', 'Number of tokens', 'time taken(s)'))
    if "signal_history" not in st.session_state:
        st.session_state['memory'] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    if "info" not in st.session_state:
        st.session_state['info'] = []
    if "source" not in st.session_state:
        st.session_state['source'] = "Database Insights"
    if "file_names" not in st.session_state:
        st.session_state.file_names = []
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "summaries" not in st.session_state:
        st.session_state.summaries = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello, how  may I help you today ?"})
    if "chat_his" not in st.session_state:
        st.session_state.chat_his = []
    if "visuals_example" not in st.session_state:
        st.session_state.example = {'data': [
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
        ], 'layout': {
            'title': 'Plot Title'
        }
    }

def log_download() -> bytes:
    """this function creates a csv that contains the logs of the different aspects of the webapp, using the logs stored in the session state
    Parameters:
        None
    Returns:
        csv_buffer(Bytes): a Bytes object that will be passed to the streamlit download button"""
    data = st.session_state['log']
    df = pd.DataFrame(data[1:], columns=data[0])
    df["Cost($)"] = df["Cost($)"].apply(lambda x: format(x, '.4f'))
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue().encode('utf-8-sig')

def check_extension(file_names: list, target_extensions: list) -> bool:
    """
    Check if the extensions of files in the given list are different from any of the target extensions.

    Parameters:
    file_names (list): A list of file names.
    target_extensions (list): A list of target extensions to compare against.

    Returns:
    bool: True if any file has an extension different from any of the target extensions, otherwise False.
    """
    for file_name in file_names:
        _, extension = os.path.splitext(file_name)
        if extension not in target_extensions:
            return True

    return False

def create_zip(pdf_contents: list, file_names: list) -> bytes:
    """ this function creates a zip that contains PDFS
            Parameters:
                pdf_contents (list of Bytes): represents a list of the Bytes that represent the content the PDF
                file_names (list of strings): a list of the file names that were uploaded by the users to use it to name the output files
            Returns:
                Zip buffer (Bytes): a zip object that will be passed to the streamlit download button"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for file_name, pdf_content in zip(file_names, pdf_contents):
            # Write each PDF content to the zip file with corresponding file name
            zf.writestr(file_name + '_summary' + ".pdf", pdf_content)

    zip_data = zip_buffer.getvalue()
    return zip_data

def summary_download() -> bytes:
    """ this function creates a pdf file for each summary generated
        Parameters:
            None
        Returns:
            Zip buffer(Bytes)"""

    pdfs = []

    for summary in (st.session_state.summaries):

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_font("Arial", "B", size=13)
        pdf.cell(200, 10, txt=f"Generated summary :", ln=1, align='L')
        pdf.set_font("Arial", size=13)
        pdf.multi_cell(200, 10, txt=f"{summary}", align='L')

        pdf_content = pdf.output(dest='S').encode('LATIN-1')
        pdfs.append(pdf_content)

    if len(pdfs) == 1:
        return pdfs[0]
    else:
        return create_zip(pdfs, st.session_state.file_names)

def chat_history_download(history: list) -> bytes:
    """ this function creates a PDF file that contains the chat history of the user
            Parameters:
                history(list of tuples): this stores the entire chat history between the user and the q&a bot
            Returns:
                pdf_content(Bytes): a Byte object that represents the PDF to be downloaded"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Conversation history", ln=1, align='C')
    for entry in history:
        pdf.multi_cell(200, 10, txt="Human: " + entry[0] + "\n \n", align="L")
        pdf.multi_cell(200, 10, txt="Chat bot: " + entry[1] + "\n \n", align="L")

    pdf_content = pdf.output(dest='S').encode('latin1')

    return pdf_content

@st.cache_data
def parse_txt(file: UploadedFile) -> str:
    """this function will parse the uploaded text file
            Parameters:
                file(UploadedFile): this represents the uploaded document
            Returns:
                    text(str): a string representing the content of the document"""
    text = file.read().decode("utf-8")
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text

@st.cache_data
def parse_uploaded_file(file: UploadedFile) -> str:
    """ this function parses the file depending on the format"""
    if file.name.endswith('.pdf'):
        parsed_files = parse_pdf(file)
    elif file.name.endswith('.docx'):
        parsed_files = parse_docx(file)
    else:
        parsed_files = parse_txt(file)
    return parsed_files

@st.cache_data
def parse_pdf(file: UploadedFile) -> list:
    """this function will parse a pdf file as Bytes
            Parameters:
                file(UploadedFile): this represents the uploaded document
            Returns:
                    output(list): a list of the parsed pdf file, where each element represents a page of that document"""
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)
    return output

@st.cache_data
def parse_docx(file: UploadedFile) -> list:
    """this function will parse the Word document
            Parameters:
                file(UploadedFile): this represents the uploaded document
            Returns:
                    text(str): a string representing the content of the document"""
    text = docx2txt.process(file)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return [text]

@st.cache_data
def text_to_docs(text: Union[str, list]) -> list:
    """Converts a string or list of strings to a list of Documents with metadata.
            Parameters:
                text(str/list): this represents the parsed file and the content of the text, it can be either a list of documents in the case
            Returns:
                    textstr): a string representing the content of the document"""
 
    if isinstance(text, str):
        text = [text]
    page_docs = [Document(page_content=page) for page in text]

    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    doc_chunks = []

    for doc in page_docs:
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)

        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk, metadata={"page": doc.metadata["page"], "chunk": i}
            )
            doc_chunks.append(doc)
    return doc_chunks
