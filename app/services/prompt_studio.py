import streamlit as st
import json
from openai import OpenAI
def remove_prompt(index):
    st.session_state.prompts_responses.pop(index)
    
# Function to import prompts from a JSON file and clear the responses
def import_from_json(file):
    try:
        data = json.load(file)
        project_name = list(data.keys())[0]
        st.session_state.project_name = project_name
        st.session_state.prompts_responses = [{"prompt": pr["prompt"], "response": ""} for pr in data[project_name].values()]
        st.success("Data imported successfully!")
    except Exception as e:
        st.error(f"Error importing data: {e}")

def export_to_json(project_name):
        data = {
            st.session_state.project_name: {
                f"Prompt {idx+1}": pr for idx, pr in enumerate(st.session_state.prompts_responses)
            }
        }
        json_data = json.dumps(data, indent=4)
        st.download_button(
            label="Export",
            data=json_data,
            file_name=f"{project_name}.json",
            mime="application/json"
        )
        
        
# Function to process the prompt and return a response (dummy implementation here)
def process_prompt(prompt, context):
 
    client = OpenAI(api_key=st.secrets["openai_api_key"])
   
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": f"""you are a document parser, consider the provided context for answering the user query: {context}\
            Strictly provide only the required data without any additional explanations or context. Do not include phrases like 'this is the answer' or 'the client name is.' Just give the direct answer to the question.
 
                """
        },
        {
        "role": "user",
        "content": f"""{prompt}
                """
        }
    ])
 
    response = response.choices[0].message.content
    return response

# def process_prompt(prompt):
#     return f"{prompt}"

# Function to add a new prompt
def add_prompt():
    st.session_state.prompts_responses.append({"prompt": "", "response": ""})

# Function to update the response for a given prompt index
def update_response(index, context):
    prompt = st.session_state[f"prompt_{index}"]
    response = process_prompt(prompt, context)
    st.session_state.prompts_responses[index]["prompt"] = prompt
    st.session_state.prompts_responses[index]["response"] = response
