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

# Custom CSS for a cyberpunk theme
st.markdown(
    """
    <style>
    body {
        color: #00ffbf;
        background-color: #0e1119;
    }
    .stButton>button {
        background-color: #ff0080;
        color: #000000;
    }
    .stTextInput>div>input {
        background-color: #1a1a1a;
        color: #00ffbf;
    }
    .stTextArea>div>textarea {
        background-color: #1a1a1a;
        color: #00ffbf;
    }
    .stSelectbox>div>div>select {
        background-color: #1a1a1a;
        color: #00ffbf;
    }
    .css-1v0v3n2 {
        background-color: #1a1a1a;
    }
    .css-1v0v3n2 p {
        color: #00ffbf;
    }
    #mouse-effect {
        position: fixed;
        pointer-events: none;
        z-index: 9999;
        border-radius: 50%;
        transition: transform 0.1s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

# Orchestration
def main():
    st.title("NeonRAG AI Agent: Your Conversational Search Companion")

    # Add language selection dropdown
    language = st.selectbox("Select Language", ["English", "Spanish", "French"])

    prompt = st.text_input("Ask NeonRAG for assistance or information:", max_chars=2000)
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
