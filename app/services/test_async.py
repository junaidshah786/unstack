import streamlit as st
import json
from openai import OpenAI
import pandas as pd
from io import BytesIO
from app.services.parse_pdf import call_unstract_api_dummy, call_unstract_api
from time import sleep
from stqdm import stqdm
from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os
import time
import concurrent.futures

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
            end_time = time.time()
            print("unstract time:", end_time- start_time)
            
            start_time = time.time()
            response = process_prompt_all(st.session_state.prompts_responses, text_output, page_number)
            results.extend(response)
            end_time= time.time()
            print("time taken for prompts:",end_time - start_time)
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
    return response




# Function to process all prompts concurrently and return structured results
def process_prompt_all(prompts_responses, context, page_number):
    print(prompts_responses)
    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks to the executor and store the future along with its index
        future_to_index = {executor.submit(process_prompt, pr["prompt"], pr["description"], context): i for i, pr in enumerate(prompts_responses)}

        # Retrieve results and store them in a list with their indices
        results_with_indices = [(future_to_index[future], future.result()) for future in concurrent.futures.as_completed(future_to_index)]

    # Sort the results by their original indices
    results_with_indices.sort()

    # Extract the sorted results and construct the final list
    sorted_results = [{"Page No.": page_number, prompts_responses[index]["prompt"]: prompts_responses[index]["prompt"], "description": prompts_responses[index]["description"], "response": result} for index, result in results_with_indices]

    return sorted_results