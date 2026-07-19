import streamlit as st
import os
import glob
import time
from downloader import download_media

# Page configuration with premium design
st.set_page_config(
    page_title="YouTube Media Downloader",
    page_icon="📥",
    layout="centered"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: bold;
        background-color: #ff4b4b;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff3333;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📥 YouTube Media Downloader")
st.write("Enter a YouTube link below, select your preferred format, and download the media to your device for free.")

# Ensure static folder exists for zero-memory static file serving
STATIC_DIR = os.path.abspath("static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Simple cleanup routine: delete files older than 1 hour in static/ to save space
current_time = time.time()
for f in glob.glob(os.path.join(STATIC_DIR, "*")):
    if os.path.isfile(f) and (current_time - os.path.getmtime(f) > 3600):
        try:
            os.remove(f)
        except Exception:
            pass

# Inputs
url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
mode = st.selectbox("Download Mode", ["Video (MP4 - Best Quality)", "Audio (MP3)"])

if st.button("Generate Download Link"):
    if not url.strip():
        st.error("Please enter a valid YouTube URL.")
    else:
        try:
            with st.spinner("Downloading and processing from YouTube... This may take a minute."):
                # Download directly to static directory
                filepath = download_media(url.strip(), mode, STATIC_DIR)
                
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    
                    # Streamlit serves static/filename at app/static/filename
                    download_url = f"app/static/{filename}"
                    
                    st.success("File processed successfully! Click the button below to download.")
                    
                    # Direct HTML download link (bypasses RAM loading, streams directly from disk)
                    st.markdown(
                        f'<a href="{download_url}" download="{filename}" target="_self">'
                        f'<button style="width: 100%; border-radius: 8px; height: 48px; font-weight: bold; '
                        f'background-color: #2e7d32; color: white; border: none; cursor: pointer; transition: 0.3s;">'
                        f'💾 Click to Save: {filename}'
                        f'</button></a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Error: Output file was not found.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
