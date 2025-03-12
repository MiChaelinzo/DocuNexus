import cv2
import base64
from azure.ai.openai import OpenAIClient
from azure.core.credentials import AzureKeyCredential
from PIL import Image
import io

# Initialize Azure OpenAI Client
azure_api_key = "YOUR_AZURE_API_KEY"  # Replace with your Azure API Key
azure_endpoint = "YOUR_AZURE_ENDPOINT"  # Replace with your Azure Endpoint
client = OpenAIClient(endpoint=azure_endpoint, credential=AzureKeyCredential(azure_api_key))

# Function to send frames to the Phi-4 model for analysis
def analyze_frame_with_phi4(image):
    # Convert the frame (PIL Image) to base64 for sending to the Phi-4 model
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()
    base64_image = base64.b64encode(img_bytes).decode()

    # Define the prompt and model inputs
    prompt = "Provide a detailed analysis of this image, identifying objects and describing the scene."
    messages = [
        {"role": "system", "content": "You are a multimodal analysis expert."},
        {"role": "user", "content": prompt, "inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
    ]

    # Call the Phi-4 model
    response = client.get_chat_completions(
        model="Phi-4-multimodal-instruct",  # Ensure this is correct for your Phi-4 model
        messages=messages,
        max_tokens=500
    )
    
    # Extract and return the model's response
    return response.choices[0].message["content"]

# Streamlit Web App
def main():
    st.set_page_config(page_title="Streamlit Phi-4 Webcam App")
    st.title("Webcam Display with Phi-4 Multimodal Analysis")
    st.caption("Powered by Azure OpenAI, Phi-4 Multimodal Model, and Streamlit")

    # Start capturing video
    cap = cv2.VideoCapture(0)
    frame_placeholder = st.empty()
    analysis_placeholder = st.empty()
    stop_button_pressed = st.button("Stop")

    while cap.isOpened() and not stop_button_pressed:
        ret, frame = cap.read()
        if not ret:
            st.write("Video Capture Ended")
            break

        # Convert frame for display and analysis
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        # Display the frame
        frame_placeholder.image(frame_rgb, channels="RGB")

        # Analyze the frame using Phi-4
        analysis_placeholder.text("Analyzing frame with Phi-4...")
        try:
            analysis = analyze_frame_with_phi4(image)
            analysis_placeholder.text(f"Phi-4 Analysis: {analysis}")
        except Exception as e:
            analysis_placeholder.text(f"Error in analysis: {e}")

        # Break if 'Stop' button is pressed
        if cv2.waitKey(1) & 0xFF == ord("q") or stop_button_pressed:
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
