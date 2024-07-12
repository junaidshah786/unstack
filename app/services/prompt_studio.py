import streamlit as st
import json
from openai import OpenAI
import pandas as pd
from app.services.parse_pdf import call_unstract_api_dummy, call_unstract_api
from time import sleep
from stqdm import stqdm
from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os
import time
import re
# Function to remove a prompt
def remove_prompt(index):
    st.session_state.prompts_responses.pop(index)

# Function to import prompts from a JSON file and clear the responses
def import_prompts(file):
    try:
        data = json.load(file)
        project_name = list(data.keys())[0]
        st.session_state.project_name = project_name
        st.session_state.prompts_responses = [{"prompt": pr["prompt"], "description": pr["description"], "response": ""} for pr in data[project_name].values()]
        st.success("Data imported successfully!")
    except Exception as e:
        st.error(f"Error importing data: {e}")

def export_prompts_to_json(project_name):
    data = {
        project_name: {
            f"Prompt {idx+1}": {
                "prompt": pr.get("prompt", ""),
                "description": pr.get("description", ""),
                "response": pr.get("response", "")
            }
            for idx, pr in enumerate(st.session_state.prompts_responses)
        }
    }

    json_data = json.dumps(data, indent=4)
    st.download_button(
        label="Export",
        data=json_data,
        file_name=f"{project_name}.json",
        mime="application/json"
    )

# # Function to process the prompt and return a response (dummy implementation here)
# def process_prompt(prompt, description, context):
#     return f"{prompt}"

# Function to add a new prompt
def add_prompt():
    st.session_state.prompts_responses.append({"prompt": "", "response": "", "description": ""})

# Function to update the response for a given prompt index
def update_response(index, context):
    prompt = st.session_state[f"prompt_{index}"]
    description = st.session_state[f"description_{index}"]
    response = process_prompt(prompt, description, context)
    st.session_state.prompts_responses[index]["prompt"] = prompt
    st.session_state.prompts_responses[index]["description"] = description
    st.session_state.prompts_responses[index]["response"] = response


# Function to split a PDF into individual pages
def split_pdf_to_pages(uploaded_file):
    reader = PdfReader(uploaded_file)
    pdf_pages = []
    for page_num in range(len(reader.pages)):
        writer = PdfWriter()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        writer.add_page(reader.pages[page_num])
        writer.write(temp_file)
        temp_file.close()
        pdf_pages.append(temp_file.name)
    return pdf_pages

# Optimize extract_data_from_pdfs function
def extract_data_from_pdfs(uploaded_files):
    results = []
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_uploaded_file:
            temp_uploaded_file.write(uploaded_file.getbuffer())
            temp_uploaded_file.seek(0)
            reader = PdfReader(temp_uploaded_file.name)
            if len(reader.pages) > 1:
                pdf_pages = split_pdf_to_pages(temp_uploaded_file.name)
            else:
                pdf_pages = [temp_uploaded_file.name]
        page_number = 1
        for page in stqdm(pdf_pages, desc="Processing pages"):
            print("uo")
            start_time = time.time()
            text_output = call_unstract_api(page)
            file_results = {}
            for index, pr in enumerate(st.session_state.prompts_responses):
                prompt = pr["prompt"]
                description = pr["description"]
                response = process_prompt(prompt, description, text_output)
                file_results['Page No.'] = page_number
                file_results[prompt] = response
            end_time= time.time()
            print("time taken:",end_time - start_time)
            results.append(file_results)
            page_number+=1

        # Clean up temporary page files
        for page in pdf_pages:
            os.remove(page)

    return results

    
# Function to process the prompt and return a response (dummy implementation here)
def process_prompt(prompt, description, context):
 
    client = OpenAI(api_key=st.secrets["openai_api_key"])
   
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": f"""you are a document parser who fetches data from forms, invoices etc, consider the provided context for answering the user query: {context}\
            Strictly provide only the required data without any additional explanations or context. Do not include phrases like 'this is the answer' or 'the client name is.' Just give the direct answer to the question.
 
                """
        },
        {
        "role": "user",
        "content": f"""Field Name: {prompt}\
                Description of Field to be fetched: {description}
                The asked feild name may or may not be present.\
                If data is not present  against the asked field name return None.
                """
        }
    ])
 
    response = response.choices[0].message.content
    # print(response)
    clean_sql_query = re.sub(r"```json\s*", "", response)
    clean_sql_query = re.sub(r"```\s*", "", clean_sql_query)
    return clean_sql_query