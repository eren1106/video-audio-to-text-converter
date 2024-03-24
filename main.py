import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os
from pytube import YouTube

# Assuming ffmpeg is installed and accessible in your system's PATH

def download_audio_from_youtube(url):
    yt = YouTube(url)
    audio_stream = yt.streams.get_audio_only()
    audio_stream.download(output_path="temp", filename="downloaded_audio.mp4")
    return os.path.join("temp", "downloaded_audio.mp4")

def convert_media_to_mp3(input_path, output_path):
    # Converts input audio/video to MP3 format
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="mp3")

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

st.title('Video / Audio to Text Converter')

# Section for uploading MP3 files or video files
uploaded_file = st.file_uploader("Choose an audio or video file", type=["mp3", "mp4", "mov", "avi", "wav"])
start_transcription_file = st.button("Start Transcription for Uploaded File", key="start_file")

# Section for YouTube video link
youtube_link = st.text_input("Or insert a YouTube video link")
start_transcription_youtube = st.button("Start Transcription for YouTube Video", key="start_youtube")

def process_audio_file(file_path):
    # Split the audio into 30-second chunks or less
    target_length_sec = 30  # You may adjust this length as necessary
    audio_chunks = split_audio(file_path, target_length_sec)

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
    return full_text

if start_transcription_file and uploaded_file is not None:
    temp_file_path = "temp_uploaded_media"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Convert to MP3 if necessary (for video files)
    if uploaded_file.type != "audio/mp3":
        mp3_path = temp_file_path + ".mp3"
        convert_media_to_mp3(temp_file_path, mp3_path)
    else:
        mp3_path = temp_file_path
    
    full_text = process_audio_file(mp3_path)
    st.text_area("Full Transcribed Text", full_text, height=300)
    
    # Clean up
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    if mp3_path != temp_file_path and os.path.exists(mp3_path):  # Remove converted MP3 if created
        os.remove(mp3_path)

if start_transcription_youtube and youtube_link:
    try:
        with st.spinner("Downloading audio from YouTube..."):
            mp4_path = download_audio_from_youtube(youtube_link)
            mp3_path = mp4_path.replace(".mp4", ".mp3")
            convert_media_to_mp3(mp4_path, mp3_path)
            if os.path.exists(mp4_path):
                os.remove(mp4_path)
        full_text = process_audio_file(mp3_path)
        st.text_area("Full Transcribed Text from YouTube Video", full_text, height=300)
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        if os.path.exists("temp"):
            # This attempts to remove the directory and fails if it's not empty,
            # ensuring only empty directories are removed.
            try:
                os.rmdir("temp")
            except OSError as e:
                st.error("Failed to clean up temporary directory. It may not be empty.")

