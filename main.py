import time
import streamlit as st
import PyPDF2
import base64
from app.services.parse_pdf import call_unstract_api, create_text_pdf, call_unstract_api_dummy
from app.services.generate_response import call_llm
from app.services.prompt_studio import update_response, add_prompt, remove_prompt, export_to_json, import_from_json


st.title("UnStack")

# Inject custom CSS to set the sidebar width
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        width: 440px;

    }
    </style>
    """,
    unsafe_allow_html=True
)
        # min-width: 440px;
        # max-width: 440px;
        
        
# Function to validate login credentials
def login(username, password):
    return username == st.secrets["db_username"] and password == st.secrets["db_password"]


# Main application
def main():
    
    

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_button = st.sidebar.button("Login")

        if login_button and login(username, password):
            st.session_state.logged_in = True
            st.toast('You have Logged in Successfully.')
            time.sleep(.5)
            # st.sidebar.success("Login successful!")
        elif login_button:
            st.toast('Invalid credentials. Please try again.')
            time.sleep(.5)
            
    if st.session_state.logged_in:
        
        st.sidebar.markdown("""
            <div style='text-align: left;'>
                <h1>Prompt Studio</h1>
                <p style='margin-bottom: 20px;'></p>
            </div>
            """, unsafe_allow_html=True)
        
        if "project_name" not in st.session_state:
            st.session_state.project_name = ""
        st.session_state.project_name = st.text_input("Project Name", placeholder="Write Your project Name")
        uploaded_file = st.file_uploader("Choose a PDF file (1 page limit)", type="pdf")
        if uploaded_file is not None:
            
            if "uploaded_file" not in st.session_state:
                st.session_state.uploaded_file = "js"
                st.toast('File Uploaded Successfully.')
                time.sleep(.6)
                # Save the uploaded file temporarily
                with open("uploaded_file.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
            # Call the API and process the PDF
            if "text_output" not in st.session_state:
                st.toast('Parsing the Pdf File.')
                st.session_state.text_output = call_unstract_api("uploaded_file.pdf")
                # st.session_state.text_output = call_unstract_api_dummy()
            
            # Display the PDF and extracted text side by side
            col1, col2 = st.columns(2)
            with col1:
                st.header("Doc View")
                if "pdf_display" not in st.session_state:
                    with open("uploaded_file.pdf", "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    st.session_state.pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="560" type="application/pdf">'
                st.markdown(st.session_state.pdf_display, unsafe_allow_html=True)

            with col2:
                st.header("Raw data")
                
                if "text_pdf_display" not in st.session_state:
                    output_pdf_path = "text_output.pdf"
                    create_text_pdf(st.session_state.text_output, output_pdf_path)
                    
                    with open(output_pdf_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    st.session_state.text_pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="560" type="application/pdf">'
                st.markdown(st.session_state.text_pdf_display, unsafe_allow_html=True)
            

    
            if "prompts_responses" not in st.session_state:
                st.session_state.prompts_responses = []

            # Buttons to add prompt and export to JSON
            col1, col2 = st.sidebar.columns([3.2, 0.8])
            with col1:
                if st.button("Add Prompt", type= "primary"):
                    add_prompt()
            with col2:
                export_to_json(st.session_state.project_name)
                
            uploaded_file_import = st.sidebar.file_uploader("Import", type="json")
            if uploaded_file_import is not None:
                if "uploaded_file_import" not in st.session_state:
                    st.session_state.uploaded_file_import= 'js'
                    print("called############")
                    import_from_json(uploaded_file_import)


            # Display all prompts and responses like a chat interface
            for idx, pr in enumerate(st.session_state.prompts_responses):
                with st.sidebar.expander(f"Prompt {idx+1}", expanded=True):
                    st.text_area(f"User Prompt:", key=f"prompt_{idx}", value=pr["prompt"], height=50)
                    if pr["response"]:
                        st.caption(f"**Response**: {pr['response']}")

                    col1, col2 = st.columns([4.2, 0.8])
                    with col1:
                        st.button("Generate Response", key=f"submit_{idx}", on_click=update_response, args=(idx,st.session_state.text_output))
                        # if updated:
                        #     st.rerun()
                    with col2:
                        rerun = st.button("🗑️", key=f"remove_{idx}", on_click=remove_prompt, args=(idx,))

                        if rerun:
                            st.rerun()

if __name__ == "__main__":
    main()
