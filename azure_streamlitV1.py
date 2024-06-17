import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import yaml
from io import BytesIO
from docx import Document
# from custom_component import secret_input

# Function to load configuration from config.yaml
def load_config():
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    return {}

# Function to save configuration to config.yaml
def save_config(speech_key, speech_region):
    config = {
        'SPEECH_KEY': speech_key,
        'SPEECH_REGION': speech_region
    }
    with open('config.yaml', 'w') as file:
        yaml.safe_dump(config, file)

# Load existing configuration
config = load_config()

st.title("Azure Speech Synthesis Configuration")

# Input fields for API key and region
speech_key = st.text_input(
    "Azure Speech API Key",
    type="password",
    value=config.get('SPEECH_KEY', ''),
    placeholder="Enter your Azure Speech API Key"
)
speech_region = st.text_input(
    "Azure Speech Region",
    value=config.get('SPEECH_REGION', ''),
    placeholder="Enter your Azure Speech Region"
)

# Button to save configuration
if st.button("Save Configuration"):
    save_config(speech_key, speech_region)
    st.success("Configuration saved successfully!")

# Ensure the configuration is loaded before proceeding
if not speech_key or not speech_region:
    st.error("Please provide Azure Speech API Key and Region in the configuration above.")
else:
    def synthesize_speech(text, output_file_path):
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name="zh-CN-YunjianNeural" 

        # Set up audio output configuration
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file_path)

        # Initialize speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Synthesize the text to the WAV file specified in the audio config
        speech_synthesizer_result = speech_synthesizer.speak_text_async(text).get()

        if speech_synthesizer_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            st.success(f"Speech synthesized to [{output_file_path}]")
            return output_file_path
        elif speech_synthesizer_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesizer_result.cancellation_details
            st.error(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    st.error(f"Error details: {cancellation_details.error_details}")
                    st.error("Did you set the speech resource key and region values?")
        return None

    def read_text_from_file(file):
        if file.name.endswith('.txt'):
            return file.read().decode('utf-8')
        elif file.name.endswith('.docx'):
            doc = Document(file)
            return '\n'.join([para.text for para in doc.paragraphs])
        else:
            st.error("Unsupported file type.")
            return None

    st.title("Azure Speech Synthesis")

    # Upload a .txt or .docx file
    uploaded_file = st.file_uploader("Upload a .txt or .docx file", type=["txt", "docx"])

    # Process the uploaded file
    if uploaded_file:
        text = read_text_from_file(uploaded_file)
        if text:
            st.text_area("File Content", text, height=200)

            if st.button("Start Speech Synthesis"):
                # Define the output path for the WAV file
                output_file_path = "output.wav"

                # Perform speech synthesis
                st.write("Performing speech synthesis...")
                st.write(f"Text to synthesize:\n{text[:1000]}")  # Display only the first 1000 characters for brevity
                result_file_path = synthesize_speech(text, output_file_path)

                # Provide a button to download the synthesized audio file and play it
                if result_file_path:
                    with open(result_file_path, "rb") as f:
                        audio_bytes = f.read()
                        st.audio(audio_bytes, format='audio/wav', start_time=0)
                        st.download_button(
                            label="Download Audio",
                            data=audio_bytes,
                            file_name="output.wav",
                            mime="audio/wav"
                        )