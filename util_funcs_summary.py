from fpdf import FPDF
import streamlit as st
import zipfile
import io
from core_funcs import generate_summary


def summary_UI():
    # an expander that will list the files uploaded and save the file names for the download functionality
    st.session_state.file_names=[]
    with st.expander("**See the files that will be summarized**:"):
        for f in st.session_state.uploaded_files:
            st.write("- "+f.name)
            st.session_state.file_names.append(f.name.split('.')[0])

    for i in range(0,2):
            st.write('')
    col1,col2,col3=st.columns([1,1,1])
    with col2:
        generate=st.button('generate summary')
    if generate:
        generate_summary(st.session_state.uploaded_files)
        st.success(f"{len(st.session_state.uploaded_files)} Document(s) summarized succesfully...")
        col4,col5,col6=st.columns([1,1,1])

        # if there are multiple files zip themand download them as a zip
        # if there is only one file download it as a pdf
        if len(st.session_state.uploaded_files)!=1:
            with col5:
                st.download_button(
                label="Download summary",
                data=summary_download(),
                file_name='summary.zip',
                mime='application/zip',help="download summary/summaries in a PDF Format ",
                )
        else:
            with col5:
                st.download_button(
                label="Download summary",
                data=summary_download(),
                file_name='summary.pdf',
                mime='application/pdf',help="download summary in a PDF Format ",
                )









def create_zip(pdf_contents, file_names):
    """ this function creates a zip that contains PDFS
            Parameters:
                pdf_contents (list of Bytes): represents a list of the Bytes that represent the content the PDF
                file_names (list of strings) : a list of the file names that were uploaded by the users to use it to name the output files
            Returns:
                Zip buffer (Bytes): a zip object that will be passed to the streamlit download button"""
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for file_name, pdf_content in zip(file_names,pdf_contents):
            # Write each PDF content to the zip file with corresponding file name
        
            zf.writestr(file_name+'_summary'+".pdf", pdf_content)

    zip_data = zip_buffer.getvalue()
    return zip_data

def summary_download():
    """ this function creates a pdf file for each summary generated
        Parameters:
            None
        Returns:
            Zip buffer(Bytes)"""

    pdfs=[]

    
    # Create the PDF object, using the BytesIO object as its "file."
    """ this function creates a PDF file that summary"""
    for summary in (st.session_state.summaries):
        
        pdf = FPDF()  
        # Add a page
        pdf.add_page()
        # set style and size of font
        pdf.set_font("Arial", size = 12)

        # insert the texts in pdf
        #pdf.cell(200, 10, txt = "Summary",
        #       ln = 1, align = 'C')

       
        pdf.set_font("Arial","B", size = 13)
        pdf.cell(200,10,txt=f"Generated summary :",ln=1,align='L')
        pdf.set_font("Arial", size = 13)
        pdf.multi_cell(200,10,txt=f"{summary}",align='L')
      
      
        pdf_content = pdf.output(dest='S').encode('LATIN-1')
        pdfs.append(pdf_content)
 
    if len(pdfs)==1:
        return pdfs[0]
    else:

     return create_zip(pdfs,st.session_state.file_names)


    



            
   