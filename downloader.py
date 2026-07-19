import yt_dlp
import os

def download_media(url: str, mode: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    
    if mode == "Audio (MP3)":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Bypass SSL errors:
            'nocheckcertificate': True,
            # Bypass datacenter 403 blocks and exclude TV client to avoid DRM error:
            'extractor_args': {
                'youtube': {
                    'player_client': ['default', '-tv', 'web_embedded']
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
            # Bypass datacenter 403 blocks and exclude TV client to avoid DRM error:
            'extractor_args': {
                'youtube': {
                    'player_client': ['default', '-tv', 'web_embedded']
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
