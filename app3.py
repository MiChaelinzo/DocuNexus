import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import boto3
from PIL import Image, ImageOps, ImageDraw
import io

# Set page config
st.set_page_config(page_title="NeuraMist⚡: AI Nexus", layout="wide", page_icon="🧠")

# Enhanced Custom CSS for cyberpunk theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    body {
        font-family: 'Orbitron', sans-serif;
        color: #00ffff;
        background-color: #000000;
    }

    .stApp {
        background-image: url('https://i.imgur.com/xMxd7vv.jpeg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .title {
        font-size: 60px;
        color: #00ffff;
        text-align: center;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff;
        animation: glitch 1s infinite;
    }

    @keyframes glitch {
        0% { text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff; }
        25% { text-shadow: -2px 0 #ff00de, 2px 2px #00ffff; }
        50% { text-shadow: 2px -2px #ff00de, -2px 2px #00ffff; }
        75% { text-shadow: -2px -2px #ff00de, 2px -2px #00ffff; }
        100% { text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff; }
    }

    .stButton>button {
        font-family: 'Orbitron', sans-serif;
        color: #00ffff;
        background-color: rgba(0, 0, 0, 0.7);
        border: 2px solid #00ffff;
        box-shadow: 0 0 10px #00ffff;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #00ffff;
        color: #000000;
        box-shadow: 0 0 20px #00ffff;
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #ff00de;
        text-shadow: 0 0 5px #ff00de;
    }

    .stTextInput>div>div>input {
        color: #00ffff;
        background-color: rgba(0, 0, 0, 0.7);
        border: 2px solid #00ffff;
    }

    .stTextArea>div>div>textarea {
        color: #00ffff;
        background-color: rgba(0, 0, 0, 0.7);
        border: 2px solid #00ffff;
    }
</style>
""", unsafe_allow_html=True)

# Import your custom module
import invoke_agent as agenthelper

# Initialize session state
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'trace_data' not in st.session_state:
    st.session_state['trace_data'] = ""

# Access AWS credentials from Streamlit secrets
aws_access_key_id = st.secrets["aws"]["access_key_id"]
aws_secret_access_key = st.secrets["aws"]["secret_access_key"]

# Initialize a boto3 session
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

credentials = session.get_credentials().get_frozen_credentials()

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Function to parse and format response
def format_response(response_body):
    try:
        data = json.loads(response_body)
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        return response_body

def main():
    st.markdown('<p class="title">NeuraMist⚡: MistralRAG AI-Agent and Snowflake Nexus</p>', unsafe_allow_html=True)

    st.write("## Upload Data for Analysis")

    uploaded_file = st.file_uploader("Choose a file or image...", type=["txt", "csv", "pdf", "jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension in ['jpg', 'jpeg', 'png']:
            handle_image_upload(uploaded_file)
        elif file_extension in ['txt', 'csv', 'pdf']:
            handle_document_upload(uploaded_file, file_extension)

    st.write("## Engage with NeuraMist⚡")

    prompt = st.text_input("Initiate your query:", max_chars=2000)
    prompt = prompt.strip()

    col1, col2 = st.columns(2)
    with col1:
        submit_button = st.button("Execute Query", type="primary")
    with col2:
        end_session_button = st.button("Terminate Session")

    if submit_button and prompt:
        process_query(prompt)

    if end_session_button:
        end_session()

    display_conversation_history()
    display_example_prompts()

def handle_image_upload(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        st.success("Image successfully uploaded and processed.")
    except IOError:
        st.error("Unable to process the image. Please ensure it's a valid file.")

def handle_document_upload(uploaded_file, file_extension):
    try:
        if file_extension == 'txt':
            content = uploaded_file.read().decode()
            st.text_area("File Content", content, height=200)
        elif file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
        elif file_extension == 'pdf':
            st.write("PDF file uploaded. Content preview not available.")
        
        st.success(f"{file_extension.upper()} file successfully uploaded and processed.")
    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")

def process_query(prompt):
    event = {
        "sessionId": "NEURAMIST_SESSION",
        "question": prompt
    }
    response = agenthelper.lambda_handler(event, None)

    try:
        if response and 'body' in response and response['body']:
            response_data = json.loads(response['body'])
            all_data = format_response(response_data['response'])
            the_response = response_data['trace_data']
        else:
            all_data = "..."
            the_response = "An error occurred. Please try again."

        st.sidebar.text_area("Trace Data:", value=all_data, height=700)
        st.session_state['history'].append({"question": prompt, "answer": the_response})
        st.session_state['trace_data'] = the_response

    except Exception as e:
        st.error(f"Error processing response: {str(e)}")

def end_session():
    st.session_state['history'].append({"question": "Session Terminated", "answer": "Thank you for using NeuraMist⚡ AI Nexus!"})
    event = {
        "sessionId": "NEURAMIST_SESSION",
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()

def display_conversation_history():
    st.write("## Neural Link History")

    human_image = Image.open('human.png')
    robot_image = Image.open('robot.png')
    circular_human_image = crop_to_circle(human_image)
    circular_robot_image = crop_to_circle(robot_image)

    for index, chat in enumerate(reversed(st.session_state['history'])):
        col1_q, col2_q = st.columns([1, 11])
        with col1_q:
            st.image(circular_human_image, width=60)
        with col2_q:
            st.text_area("You:", value=chat["question"], height=100, key=f"question_{index}", disabled=True)

        col1_a, col2_a = st.columns([1, 11])
        with col1_a:
            st.image(circular_robot_image, width=80)
        with col2_a:
            if isinstance(chat["answer"], pd.DataFrame):
                st.dataframe(chat["answer"], key=f"answer_df_{index}")
            else:
                st.text_area("NeuraMist⚡:", value=chat["answer"], height=200, key=f"answer_{index}", disabled=True)

def display_example_prompts():
    st.write("## Query Templates")

    example_prompts = [
        "Analyze global climate change trends over the last decade.",
        "Optimize recycling processes for urban environments.",
        "Design strategies for minimizing plastic waste in oceans.",
        "Develop AI-driven solutions for combating air pollution in megacities."
    ]

    st.markdown("""
        Initiate your cyber-exploration with these prompts:
        * **Data Analysis:** "Decrypt the impact of deforestation on global biodiversity."
        * **Optimization:** "Enhance home energy efficiency using smart AI algorithms."
        * **Comparative Study:** "Conduct a deep-dive analysis: Electric vs. Traditional vehicles' environmental impact."
        * **Strategic Planning:** "Architect a sustainable living framework for future megacities."
        """)

    for prompt in example_prompts:
        st.write(f"* {prompt}")

    feedback = st.text_input("Provide feedback to improve NeuraMist⚡:", max_chars=2000)
    if st.button("Submit Feedback"):
        st.success("Feedback successfully integrated into our neural network. Thank you for enhancing NeuraMist⚡!")

if __name__ == "__main__":
    main()
