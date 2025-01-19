import invoke_agent as agenthelper
import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import boto3
from PIL import Image, ImageOps, ImageDraw
import requests
import base64
import snowflake.connector
import trulens

# Access AWS credentials from Streamlit secrets
aws_access_key_id = st.secrets["aws"]["access_key_id"]
aws_secret_access_key = st.secrets["aws"]["secret_access_key"]

# Initialize a boto3 session
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

credentials = session.get_credentials().get_frozen_credentials()


# Streamlit page configuration with a dark theme
st.set_page_config(
    page_title="DocuNexus AI-Agent: Agent designed to streamline document workflows and enhance productivity",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        background-image: url('https://i.imgur.com/530DGSL.png');
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

# JavaScript for mouse effect
st.markdown(
    """
    <script>
    const mouseEffect = document.createElement('div');
    mouseEffect.id = 'mouse-effect';
    mouseEffect.style.width = '20px';
    mouseEffect.style.height = '20px';
    mouseEffect.style.backgroundColor = '#00ffbf';
    document.body.appendChild(mouseEffect);

    document.addEventListener('mousemove', (e) => {
        mouseEffect.style.left = e.pageX + 'px';
        mouseEffect.style.top = e.pageY + 'px';
    });
    </script>
    """,
    unsafe_allow_html=True,
)

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

# Function to send document to DocuSign for signature
def send_to_docusign(file_path, recipient_email, recipient_name):
    docusign_api_key = st.secrets["docusign"]["api_key"]
    docusign_base_url = "https://demo.docusign.net/restapi"

    headers = {
        "Authorization": f"Bearer {docusign_api_key}",
        "Content-Type": "application/json"
    }

    envelope_definition = {
        "emailSubject": "Please sign this document",
        "documents": [
            {
                "documentId": "1",
                "name": "document.pdf",
                "fileExtension": "pdf",
                "documentBase64": base64.b64encode(open(file_path, "rb").read()).decode()
            }
        ],
        "recipients": {
            "signers": [
                {
                    "email": recipient_email,
                    "name": recipient_name,
                    "recipientId": "1",
                    "tabs": {
                        "signHereTabs": [
                            {
                                "documentId": "1",
                                "pageNumber": "1",
                                "xPosition": "100",
                                "yPosition": "100"
                            }
                        ]
                    }
                }
            ]
        },
        "status": "sent"
    }

    response = requests.post(f"{docusign_base_url}/v2.1/accounts/{account_id}/envelopes", headers=headers, json=envelope_definition)
    return response.json()

# Snowflake connection
def connect_to_snowflake():
    try:
        con = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )
        return con
    except Exception as e:
        st.error(f"Error connecting to Snowflake: {e}")
        return None

# Function to execute a query on Snowflake
def execute_snowflake_query(query):
    con = connect_to_snowflake()
    if con:
        try:
            cur = con.cursor()
            cur.execute(query)
            result = cur.fetchall()
            con.close()
            return result
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return None

# Orchestration
def main():
    st.markdown('<p class="title">DocuNexus AI-Agent 🤖: Agent designed to streamline document workflows and enhance productivity</p>', unsafe_allow_html=True)

    # Add language selection dropdown
    language = st.selectbox("Select Language", ["English", "Spanish", "French"])

    prompt = st.text_input("Ask DocuNexus AI-Agent 🤖 for assistance or information:", max_chars=2000)
    prompt = prompt.strip()

    submit_button = st.button("Submit", type="primary")
    end_session_button = st.button("End Session")

    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'trace_data' not in st.session_state:
        st.session_state['trace_data'] = ""

    if submit_button and prompt:
        # Translate user input to English
        #if language != "English":
            #prompt = translate_text(prompt, "English")

        event = {
            "sessionId": "NEON_SESSION",
            "question": prompt
        }
        response = agenthelper.lambda_handler(event, None)

        try:
            if response and 'body' in response and response['body']:
                response_data = json.loads(response['body'])
                print("TRACE & RESPONSE DATA ->  ", response_data)
            else:
                print("Invalid or empty response received")
        except json.JSONDecodeError as e:
            print("JSON decoding error:", e)
            response_data = None

        try:
            all_data = format_response(response_data['response'])
            the_response = response_data['trace_data']
        except:
            all_data = "..."
            the_response = "Apologies, but an error occurred. Please rerun the application"

        st.sidebar.text_area("Trace Data:", value=all_data, height=700)
        st.session_state['history'].append({"question": prompt, "answer": the_response})
        st.session_state['trace_data'] = the_response

        # Analyze sentiment of user input
        #sentiment = sa.analyze_sentiment(prompt)

        # Generate a sample graph
        #generate_graph()

        # Generate an image based on user input (placeholders for now)
        #generate_image(prompt)

        # Translate AI Agent's response to the selected language
        #if language != "English":
            #the_response = translate.translate_text(the_response, language)

        # Convert the response to speech
        #audio_file = tts.text_to_speech(the_response)

    if end_session_button:
        st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using NeonRAG AI Agent!"})
        event = {
            "sessionId": "NEON_SESSION",
            "question": "placeholder to end session",
            "endSession": True
        }
        agenthelper.lambda_handler(event, None)
        st.session_state['history'].clear()

    display_conversation_history()
    display_example_prompts()

    # DocuSign integration
    st.sidebar.header("DocuSign Integration")
    file_path = st.sidebar.file_uploader("Upload a document for signature", type=["pdf"])
    recipient_email = st.sidebar.text_input("Recipient Email")
    recipient_name = st.sidebar.text_input("Recipient Name")

    if st.sidebar.button("Send to DocuSign"):
        if file_path and recipient_email and recipient_name:
            response = send_to_docusign(file_path, recipient_email, recipient_name)
            st.sidebar.write("DocuSign Response:", response)
        else:
            st.sidebar.error("Please provide all required information.")

    # Snowflake integration
    st.sidebar.header("Snowflake Integration")
    query = st.sidebar.text_area("Enter your SQL query:", height=150)
    if st.sidebar.button("Execute Query"):
        if query:
            result = execute_snowflake_query(query)
            if result:
                st.sidebar.write("Query Result:", result)
            else:
                st.sidebar.error("Failed to execute query.")
        else:
            st.sidebar.error("Please enter a query.")

def display_conversation_history():
    st.write("## Conversation History")

    human_image = Image.open('human.png')
    robot_image = Image.open('robot.png')
    circular_human_image = crop_to_circle(human_image)
    circular_robot_image = crop_to_circle(robot_image)

    for index, chat in enumerate(reversed(st.session_state['history'])):
        col1_q, col2_q = st.columns([1, 11])
        with col1_q:
            st.image(circular_human_image, width=60)
        with col2_q:
            st.text_area("You:", value=chat["question"], height=150, key=f"question_{index}", disabled=True)

        col1_a, col2_a = st.columns([1, 11])
        with col1_a:
            st.image(circular_robot_image, width=60)
        with col2_a:
            if isinstance(chat["answer"], pd.DataFrame):
                st.dataframe(chat["answer"], key=f"answer_df_{index}")
            else:
                st.text_area("DocuNexus AI Agent:", value=chat["answer"], height=250, key=f"answer_{index}", disabled=True)

def display_example_prompts():
    st.write("## Example Prompts")

    example_prompts = [
        "I'm looking for intel on corporate espionage.",
        "What are the best practices for hacking the matrix?",
        "Can you provide some tips for evading cyber-surveillance?",
        "What are the most effective ways to combat cyber-crime syndicates?"
    ]

    st.markdown("""
        Here are some examples to get you started:
        * **Information:** "Tell me about the impacts of corporate monopolies on the black market."
        * **Tips:** "How can I reduce my digital footprint in a dystopian world?"
        * **Comparison:** "Compare the environmental impact of electric cars vs. traditional cars in a post-apocalyptic world."
        * **Strategies:** "What are some strategies for promoting underground resistance movements?"
        """)

    for prompt in example_prompts:
        st.write(f"* {prompt}")

if __name__ == "__main__":
    main()
