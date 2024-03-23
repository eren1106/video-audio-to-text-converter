import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os

# Assuming ffmpeg is installed and accessible in your system's PATH

def split_audio(audio_file_path, target_length_sec):
    audio = AudioSegment.from_mp3(audio_file_path)
    chunk_length_ms = target_length_sec * 1000  # Convert target length to milliseconds
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    return chunks

def transcribe_audio(wav_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text

st.title('Audio to Text Converter')

uploaded_file = st.file_uploader("Choose an MP3 file", type=["mp3"])

if uploaded_file is not None:
    # Save the uploaded file to disk
    with open("temp_audio.mp3", "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    # Split the audio into 30-second chunks or less
    target_length_sec = 30  # You may adjust this length as necessary
    audio_chunks = split_audio("temp_audio.mp3", target_length_sec)

    full_text = ""
    for i, chunk in enumerate(audio_chunks):
        chunk_filename = f"chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav", parameters=["-ar", "16000"])  # Export with a sampling rate of 16000 Hz
        
        try:
            with st.spinner(f'Converting chunk {i+1}/{len(audio_chunks)} to text...'):
                text = transcribe_audio(chunk_filename)
                full_text += text + " "
        except Exception as e:
            st.error(f'Failed to convert chunk {i+1} to text due to error: {str(e)}')
        finally:
            if os.path.exists(chunk_filename):
                os.remove(chunk_filename)

    st.text_area("Full Transcribed Text", full_text, height=300)

    # Clean up the original audio file
    if os.path.exists("temp_audio.mp3"):
        os.remove("temp_audio.mp3")
