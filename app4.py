import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import boto3
from PIL import Image, ImageOps, ImageDraw
import io
#import pytesseract
#import PyPDF2
import invoke_agent as agenthelper

# Set page config
st.set_page_config(page_title="NeuraMist⚡: AI Nexus", layout="wide", page_icon="🧠")

# Enhanced Custom CSS for cyberpunk theme with cyberpunk mouse cursor
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    body {
        font-family: 'Orbitron', sans-serif;
        color: #00ffff;
        background-color: #000000;
        cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF7WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIzLTA2LTIyVDE1OjUxOjE4KzAyOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMy0wNi0yMlQxNTo1MzowOCswMjowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMy0wNi0yMlQxNTo1MzowOCswMjowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpmNzQ0NDhmZC1hNzM1LWNkNGYtOTY3Yi1iNjNjOTVlNzY3YzAiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDpmOTEzZTkyNy1kODM3LWVmNDctYjdhMC02MjRjNzA1NzUyZTAiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo3YzUzODExNi1iZDFjLTMwNGItODMyNy0wMjg5MzA0MjA3ZGMiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdjNTM4MTE2LWJkMWMtMzA0Yi04MzI3LTAyODkzMDQyMDdkYyIgc3RFdnQ6d2hlbj0iMjAyMy0wNi0yMlQxNTo1MToxOCswMjowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTkgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpmNzQ0NDhmZC1hNzM1LWNkNGYtOTY3Yi1iNjNjOTVlNzY3YzAiIHN0RXZ0OndoZW49IjIwMjMtMDYtMjJUMTU6NTM6MDgrMDI6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PB4oMAAACOUlEQVRYhe2XPWgUURSFv7lrl0AWJAYRROMPiBFsFNRCjKKdWImFWNlZKyKColUQsTUgWFpaKIJYiYUoQkQMKBgRVEKIoBLBnyIs2WyOxcyG2cnMzs4k2cLE0+y8N3Pvu+fNvfPeWElVuJLBOEvJzDpmds7MnGv3+TUze+5/+9s5d8aS5uG4mdmFRAJmNmlmxxK4b5jZqJldNbO+XMNKTw9r5+d5BEwsnxJWAsPAD2AXsBMYAxYz5gEGgVHgNLAWOAocAt4DvcAH4F6UZLrXwOMiw0sF0Av0AW3gBfAkEh8CrnjxRuCIlxNYBbQC8TDQAZaBd8Ai0PEJ54BPqcdLA/gD/PROzNtRwDPfbuA9cBR4DXwEvvoA7gPPgLfADHABOJTSfzNZ+LLZrr5+7TbduuV6slVmNuCcm41OO+6D+OJxfAS2AJsKglIWu4BNwPZkUHW/UrHevj7Vamk5VuWYmVkryTBVHaqK6n6U5wIUazdwz8w2F4inYMWKOVHaQBr9wDrgaNT/2hsCj9z8TpKRkqGqDhQYUEkH1Zcq6kNEotuqU6pNv4cO5AmobkHVpbRXYkRVG6qTqrOqj1SvqI6pTqs+9fF+1YZvtwrGOun7TvrxVzmuVHU9I4AV1T09fVX16BoYQHVviYAfQhAJQ9WJ3aodxcf6yPBKZNkwMZZuVHVQte0zWPVCYYMJTqk2VWt+rYbqjRUG8BvMuuqE6vdCAdSAb8AOoAN8BoYIWTILMz4BLgN/gQHC+Z7nP9RDDRWeMlXHAAAAAElFTkSuQmCC'), auto;
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
    st.markdown('#### NeuraMist⚡: MistralRAG AI-Agent and Snowflake Nexus', unsafe_allow_html=True)

    # Add language and response length preferences
    language = st.sidebar.selectbox("Select Language", ["English", "Spanish", "French"])
    response_length = st.sidebar.selectbox("Select Response Length", ["Short", "Medium", "Long"])

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
        process_query(prompt, language, response_length)

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
        
        # Extract text from image using OCR
        #text = pytesseract.image_to_string(image)
        #st.write("Extracted Text:", text)
        
        st.success("Image successfully uploaded and processed.")
        return text
    except IOError:
        st.error("Unable to process the image. Please ensure it's a valid file.")
        return None

def handle_document_upload(uploaded_file, file_extension):
    try:
        if file_extension == 'txt':
            content = uploaded_file.read().decode()
            st.text_area("File Content", content, height=200)
        elif file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
        elif file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfFileReader(uploaded_file)
            content = ""
            for page in range(pdf_reader.numPages):
                content += pdf_reader.getPage(page).extractText()
            st.text_area("PDF Content", content, height=200)
        
        st.success(f"{file_extension.upper()} file successfully uploaded and processed.")
        return content
    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")
        return None

def process_query(prompt, language, response_length):
    event = {
        "sessionId": "NEURAMIST_SESSION",
        "question": prompt,
        "language": language,
        "responseLength": response_length
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
            st.image(circular_human_image, width=80)
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
