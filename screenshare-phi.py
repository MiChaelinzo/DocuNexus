import streamlit as st
from mss import mss
from PIL import Image
import time
import cv2
import numpy as np
import base64
from io import BytesIO

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl,
    ImageDetailLevel,
)
from azure.core.credentials import AzureKeyCredential

# Cyberpunk color palette (neon on dark)
NEON_GREEN = "#39FF14"
NEON_PINK = "#FF69B4"
NEON_BLUE = "#00FFFF"
DARK_BG = "#111111"  # Slightly lighter than pure black for better readability

# --- Streamlit Styling ---
st.set_page_config(
    page_title="CyberScreen",
    page_icon="🌃",
    layout="wide",
    initial_sidebar_state="collapsed",
    #theme="dark",  # Use Streamlit's built-in dark theme as a base
)

# Custom CSS for cyberpunk aesthetics
st.markdown(
    f"""
    <style>
        body {{
            color: {NEON_GREEN};
            background-color: {DARK_BG};
        }}
        .stApp {{
            background-color: {DARK_BG};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {NEON_PINK};
        }}
        .stButton > button {{
            color: {NEON_BLUE};
            border-color: {NEON_BLUE};
            background-color: transparent;
        }}
        .stButton > button:hover {{
            background-color: {NEON_BLUE};
            color: {DARK_BG};
        }}
        .stTextInput > div > div > input {{
            color: {NEON_GREEN};
            background-color: #222222;
            border-color: {NEON_GREEN};
        }}
        .stTextArea > div > div > textarea {{
            color: {NEON_GREEN};
            background-color: #222222;
            border-color: {NEON_GREEN};
        }}
        .stChatMessage {{
            background-color: #222222;
            border-color: {NEON_GREEN};
            color: {NEON_GREEN};
        }}
        .stChatMessage.user {{
            border-left-color: {NEON_PINK}; /* Differentiate user messages */
        }}
        .stSpinner > div > div {{ /* Style the spinner */
            border-color: {NEON_BLUE};
            border-right-color: transparent; /* Make it neon blue */
        }}
        .streamlit-expanderHeader {{
            color: {NEON_PINK} !important; /* Ensure expander header text is neon pink */
        }}
        .streamlit-expanderContent {{
            color: {NEON_GREEN}; /* Expander content text color */
        }}


    </style>
    """,
    unsafe_allow_html=True,
)


# --- Azure AI Inference - Phi-4 Model Client Setup ---
AZURE_ENDPOINT = "https://models.inference.ai.azure.com"
AZURE_MODEL_NAME = "Phi-4-multimodal-instruct"
AZURE_API_KEY = st.secrets["azure_ai"]["api_key"]
phi_model = None
phi_client = None

if not AZURE_API_KEY:
    st.error("ERROR: Access Keycard Missing. Neural Net Interface Offline.") # Cyberpunk error message
    phi_model = None
else:
    try:
        phi_client = ChatCompletionsClient(
            endpoint=AZURE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_API_KEY),
        )
        phi_model = AZURE_MODEL_NAME
    except Exception as e:
        st.error(f"ERROR: Neural Net Client Init Failure: {e}") # Cyberpunk error message
        phi_model = None


# --- Streamlit App Content ---
st.title("CyberScreen: Visual Data Stream Analysis 🌃") # Cyberpunk title

# Session state management
if 'sharing' not in st.session_state:
    st.session_state.update({
        'sharing': False,
        'chat_history': [],
        'current_frame': None
    })

def toggle_sharing():
    st.session_state.sharing = not st.session_state.sharing

col1, col2 = st.columns([3, 2])

with col1:
    st.button("Engage/Disengage Stream", on_click=toggle_sharing) # Cyberpunk button text
    image_placeholder = st.empty()

with col2:
    st.subheader("Data Matrix Interface (Phi-4 Core)") # Cyberpunk subtitle
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Query visual data stream..."): # Cyberpunk chat input prompt
        if st.session_state.current_frame is None:
            st.error("ERROR: Data Stream Inactive. Engage Stream First!") # Cyberpunk error
        elif phi_model is None:
            st.error("ERROR: Phi-4 Core Offline. Check System Connection.") # Cyberpunk error
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.spinner("Processing visual data through Phi-4 Neural Net..."): # Cyberpunk spinner text
                try:
                    img_pil = Image.fromarray(st.session_state.current_frame)

                    buffered = BytesIO()
                    img_pil.save(buffered, format="PNG")
                    img_bytes = buffered.getvalue()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    data_url = f"data:image/png;base64,{img_base64}"

                    messages = [
                        UserMessage(
                            content=[
                                TextContentItem(text=prompt),
                                ImageContentItem(
                                    image_url=ImageUrl(url=data_url)
                                ),
                            ],
                        ),
                    ]

                    response = phi_client.complete(
                        model=phi_model,
                        messages=messages
                    )

                    ai_response_text = response.choices[0].message.content

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response_text
                    })
                    st.rerun()

                except Exception as e:
                    st.error(f"ERROR: Data stream analysis failure: {e}") # Cyberpunk error
                    st.error(f"Debug trace: {e}") # Keep technical detail for debugging

monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}

with mss() as sct:
    while st.session_state.sharing:
        screen_frame = sct.grab(monitor)
        img = Image.frombytes("RGB", screen_frame.size, screen_frame.rgb)
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.session_state.current_frame = frame
        display_img = Image.fromarray(frame)
        display_img.thumbnail((1024, 576))
        image_placeholder.image(display_img)
        time.sleep(0.1)

if not st.session_state.sharing:
    image_placeholder.empty()
    st.session_state.current_frame = None
