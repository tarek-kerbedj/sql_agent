import re
import docx2txt
from pypdf import PdfReader
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter,RecursiveCharacterTextSplitter
from fpdf import FPDF
import streamlit as st
def chat_history_download(history):

    """ this function creates a PDF file that contains the chat history of the user
            Parameters:
                history(list of tuples) : this stores the entire chat history between the user and the q&a bot
            Returns:
                pdf_content(Bytes): a Byte object that represents the PDF  to be downloaded"""""
    pdf = FPDF()  
    # Add a page
    pdf.add_page()

    # set style and size of font
    pdf.set_font("Arial", size = 12)
    # open the text file in read mode
    #f = open("chat.txt", "r")
    
    # insert the texts in pdf
    pdf.cell(200, 10, txt = "Conversation history",
            ln = 1, align = 'C')
    for entry in history:
        #pdf.set_fill_color(255, 255, 0)
        pdf.multi_cell(200, 10, txt = "Human: "+entry[0]+"\n \n",align="L")
 
        #pdf.multi_cell(0, 10, txt="This is right-aligned text.", ln=1)
        pdf.multi_cell(200, 10, txt = "Chat bot: "+entry[1]+"\n \n",align="L")
        
    pdf_content = pdf.output(dest='S').encode('latin1')

    return pdf_content

@st.cache_data
def parse_txt(file):
    """this function will parse the uploaded text file
            Parameters:
                file(UploadedFile) : this represents the uploaded document
            Returns:
                    text(str): a string representing the content of the document"""""
    text = file.read().decode("utf-8")
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text

@st.cache_data
def parse_uploaded_file(file):
    """ this function parses the file depending on the format"""
    if file.name.endswith('.pdf'):
        parsed_files = parse_pdf(file)
    elif file.name.endswith('.docx'):
        parsed_files = parse_docx(file)
    else:
        parsed_files=parse_txt(file)
    return parsed_files

@st.cache_data
def parse_pdf(file):
    """this function will parse a pdf file as Bytes
            Parameters:
                file(UploadedFile) : this represents the uploaded document
             
            Returns:
                    output(list): a list of the parsed pdf file , where each element represents a page of that document"""
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        # Merge hyphenated words
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        # Fix newlines in the middle of sentences
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        # Remove multiple newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)
    return output

@st.cache_data
def parse_docx(file):
    """this function will parse the Word document
            Parameters:
                file(UploadedFile) : this represents the uploaded document
            Returns:
                    text(str): a string representing the content of the document"""""
    #len_pages(file)
    text = docx2txt.process(file)
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return [text]

@st.cache_data
def text_to_docs(text):
    """Converts a string or list of strings to a list of Documents
    with metadata.
            Parameters:
                text(str/list) : this represents the parsed file and the content of the text , it can be either a list of documents in the case
            Returns:
                    text(str): a string representing the content of the document"""""
 
    if isinstance(text, str):
        # Take a single string as one page
        text = [text]
    page_docs = [Document(page_content=page) for page in text]

    # Add page numbers as metadata
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    # Split pages into chunks
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