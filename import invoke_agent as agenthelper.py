import invoke_agent as agenthelper
import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import boto3
from PIL import Image, ImageOps, ImageDraw
import text_to_speech as tts
import translate_text as translate
import sentiment_analysis as sa

# Access AWS credentials from Streamlit secrets
aws_access_key_id = st.secrets["aws"]["access_key_id"]
aws_secret_access_key = st.secrets["aws"]["secret_access_key"]

# Initialize a boto3 session
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

credentials = session.get_credentials().get_frozen_credentials()

# Streamlit page configuration
st.set_page_config(
    page_title="MistralRAG AI Agent: Your Conversational Search Companion",
    page_icon=":robot:",
    layout="wide"
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

# Orchestration
def main():
    st.title("MistralRAG AI Agent: Your Conversational Search Companion")

    # Add language selection dropdown
    language = st.selectbox("Select Language", ["English", "Spanish", "French"])

    prompt = st.text_input("Ask MistralRAG for assistance or information:", max_chars=2000)
    prompt = prompt.strip()

    submit_button = st.button("Submit", type="primary")
    end_session_button = st.button("End Session")

    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'trace_data' not in st.session_state:
        st.session_state['trace_data'] = ""

    if submit_button and prompt:
        # Translate user input to English
        if language != "English":
            # Placeholder for translation function
            prompt = translate_text(prompt, "English")

        event = {
            "sessionId": "MISTRAL_SESSION",
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
        sentiment = sa.analyze_sentiment(prompt)

        # Generate a sample graph
        generate_graph()

        # Generate an image based on user input (placeholders for now)
        generate_image(prompt)

        # Translate AI Agent's response to the selected language
        if language != "English":
            # Placeholder for translation function
            the_response = translate.translate_text(the_response, language)

        # Convert the response to speech
        audio_file = tts.text_to_speech(the_response)


    if end_session_button:
        st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using MistralRAG AI Agent!"})
        event = {
            "sessionId": "MISTRAL_SESSION",
            "question": "placeholder to end session",
            "endSession": True
        }
        agenthelper.lambda_handler(event, None)
        st.session_state['history'].clear()

    display_conversation_history()
    display_example_prompts()

def display_conversation_history():
    st.write("## Conversation History")

    human_image = Image.open('human.png')
    robot_image = Image.open('robot.png')
    circular_human_image = crop_to_circle(human_image)
    circular_robot_image = crop_to_circle(robot_image)

    for index, chat in enumerate(reversed(st.session_state['history'])):
        col1_q, col2_q = st.columns([1, 11])
        with col1_q:
            st.image(circular_human_image, width=50)
        with col2_q:
            st.text_area("You:", value=chat["question"], height=150, key=f"question_{index}", disabled=True)

        col1_a, col2_a = st.columns([1, 11])
        with col1_a:
            st.image(circular_robot_image, width=100)
        with col2_a:
            if isinstance(chat["answer"], pd.DataFrame):
                st.dataframe(chat["answer"], key=f"answer_df_{index}")
            else:
                st.text_area("MistralRAG AI Agent:", value=chat["answer"], height=250, key=f"answer_{index}", disabled=True)

def display_example_prompts():
    st.write("## Example Prompts")

    example_prompts = [
        "I'm looking for information on climate change.",
        "What are the best practices for recycling?",
        "Can you provide some tips for reducing plastic waste?",
        "What are the most effective ways to combat air pollution?"
    ]

    st.markdown("""
        Here are some examples to get you started:
        * **Information:** "Tell me about the impacts of deforestation on biodiversity."
        * **Tips:** "How can I reduce my energy consumption at home?"
        * **Comparison:** "Compare the environmental impact of electric cars vs. traditional cars."
        * **Strategies:** "What are some strategies for promoting sustainable living?"
        """)

    for prompt in example_prompts:
        st.write(f"* {prompt}")

if __name__ == "__main__":
    main()