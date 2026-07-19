import yt_dlp
import os
import shutil

# Dynamically locate node or nodejs executable
NODE_PATH = shutil.which("node") or shutil.which("nodejs")
if not NODE_PATH:
    # Try common absolute paths if not found in PATH environment variable
    for path in ["/usr/bin/node", "/usr/bin/nodejs", "/usr/local/bin/node", "/usr/local/bin/nodejs"]:
        if os.path.exists(path):
            NODE_PATH = path
            break

def download_media(url: str, mode: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    
    # Configure JS runtime dictionary
    js_runtimes_config = {}
    if NODE_PATH:
        js_runtimes_config['node'] = {'path': NODE_PATH}
    else:
        # Fallback to default check if path not found
        js_runtimes_config['node'] = {}

    if mode == "Audio (MP3)":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                'nopostoverwrites': False,
            }],
            # Bypass SSL errors:
            'nocheckcertificate': True,
            # Allow fetching external JS challenge solvers:
            'remote_components': ['ejs:github'],
            # Enable Node.js JS runtime:
            'js_runtimes': js_runtimes_config,
            # Bypass datacenter 403 blocks and use web/android clients:
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'web_embedded']
                }
            },
        }
    else: # Video (MP4 - Best Quality)
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            # Bypass SSL errors:
            'nocheckcertificate': True,
            # Allow fetching external JS challenge solvers:
            'remote_components': ['ejs:github'],
            # Enable Node.js JS runtime:
            'js_runtimes': js_runtimes_config,
            # Bypass datacenter 403 blocks and use web/android clients:
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'web_embedded']
                }
            },
        }
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        # Adjust extension for postprocessed audio
        if mode == "Audio (MP3)":
            filename = os.path.splitext(filename)[0] + ".mp3"
        else:
            filename = os.path.splitext(filename)[0] + ".mp4"
            
        return filename

