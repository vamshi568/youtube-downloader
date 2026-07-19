import streamlit as st
import os
import tempfile
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

# Inputs
url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
mode = st.selectbox("Download Mode", ["Video (MP4 - Best Quality)", "Audio (MP3)"])

if st.button("Generate Download Link"):
    if not url.strip():
        st.error("Please enter a valid YouTube URL.")
    else:
        try:
            with st.spinner("Downloading and processing from YouTube... This may take a minute."):
                # Download to a temporary folder
                temp_dir = tempfile.mkdtemp()
                filepath = download_media(url.strip(), mode, temp_dir)
                
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    with open(filepath, "rb") as file:
                        btn = st.download_button(
                            label=f"💾 Download {filename}",
                            data=file,
                            file_name=filename,
                            mime="audio/mpeg" if mode == "Audio (MP3)" else "video/mp4"
                        )
                    st.success("File processed successfully! Click the button above to download.")
                else:
                    st.error("Error: Output file was not found.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
