import yt_dlp
import os
import shutil
import subprocess

from pot_server import ensure_pot_server_running

# Dynamically locate node or nodejs executable
NODE_PATH = shutil.which("node") or shutil.which("nodejs")
if not NODE_PATH:
    # Try common absolute paths if not found in PATH environment variable
    for path in ["/usr/bin/node", "/usr/bin/nodejs", "/usr/local/bin/node", "/usr/local/bin/nodejs"]:
        if os.path.exists(path):
            NODE_PATH = path
            break

print(f"DEBUG: NODE_PATH detected as: {NODE_PATH}")
if NODE_PATH:
    try:
        node_version = subprocess.check_output([NODE_PATH, "--version"], text=True).strip()
        print(f"DEBUG: Node.js version: {node_version}")
    except Exception as e:
        print(f"DEBUG: Failed to run Node.js from {NODE_PATH}: {e}")
else:
    print("DEBUG: No Node.js executable found on the system.")

# YouTube has been rolling out "SABR-only" streaming + Proof-of-Origin (PO) token
# enforcement through 2025-2026 (see https://github.com/yt-dlp/yt-dlp/issues/12482).
# 'mweb' and 'web' are the clients community reports say benefit most from having
# a real PO token (see the bgutil PO-token server started below); 'tv' comes next
# since it can hit DRM experiments on some videos (issue #12563); 'android'/
# 'android_sdkless' are being phased out community-wide and are skipped entirely.
# This list will likely need to change again as YouTube keeps adjusting things -
# check https://github.com/yt-dlp/yt-dlp/issues/12482 for the current guidance.
CLIENT_STRATEGIES = [
    ["mweb"],
    ["web"],
    ["tv"],
    ["tv", "web"],
]

# Best-effort: start a local PO-token generator so yt-dlp's bgutil plugin
# (pip package `bgutil-ytdlp-pot-provider`, see requirements.txt) can attach a
# real token to requests instead of getting SABR-only/no-URL responses. This
# never raises - POT_SERVER_AVAILABLE is just informational/logged.
POT_SERVER_AVAILABLE = ensure_pot_server_running()
print(f"DEBUG: PO-token server available: {POT_SERVER_AVAILABLE}")


class DownloadBlockedError(Exception):
    """Raised when every client strategy was rejected by YouTube (403/blocked)."""


def _build_ydl_opts(mode: str, out_dir: str, player_clients, cookiefile: str | None):
    js_runtimes_config = {"node": {"path": NODE_PATH} if NODE_PATH else {}}

    common = {
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        # Bypass SSL errors:
        "nocheckcertificate": True,
        # Allow fetching external JS challenge (n-sig) solvers:
        "remote_components": ["ejs:github"],
        # Enable Node.js JS runtime for the challenge solver:
        "js_runtimes": js_runtimes_config,
        "extractor_args": {"youtube": {"player_client": player_clients}},
        "verbose": True,
    }

    if cookiefile:
        # Using cookies from a real logged-in session reduces (but does not
        # eliminate) the chance of YouTube rejecting the request.
        common["cookiefile"] = cookiefile

    if mode == "Audio (MP3)":
        common.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
                "nopostoverwrites": False,
            }],
        })
    else:  # Video (MP4 - Best Quality)
        common.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    return common


def download_media(url: str, mode: str, out_dir: str, cookiefile: str | None = None) -> str:
    os.makedirs(out_dir, exist_ok=True)

    last_error = None
    for player_clients in CLIENT_STRATEGIES:
        ydl_opts = _build_ydl_opts(mode, out_dir, player_clients, cookiefile)
        print(f"DEBUG: Attempting download with player_client={player_clients}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                if mode == "Audio (MP3)":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                else:
                    filename = os.path.splitext(filename)[0] + ".mp4"

                if os.path.exists(filename):
                    return filename
                last_error = RuntimeError(
                    f"yt-dlp reported success but no output file was found for player_client={player_clients}"
                )
        except yt_dlp.utils.DownloadError as e:
            print(f"DEBUG: player_client={player_clients} failed: {e}")
            last_error = e
            continue  # try the next client strategy

    # Every strategy failed. This is almost always YouTube-side blocking
    # (SABR-only streaming / PO token enforcement, or the hosting IP being
    # rate-limited), not a bug in this app. See:
    # https://github.com/yt-dlp/yt-dlp/issues/12482
    raise DownloadBlockedError(
        "YouTube rejected every download strategy we tried (mweb/web/tv clients). "
        f"Local PO-token server was {'available' if POT_SERVER_AVAILABLE else 'NOT available'} "
        "for this attempt. This is almost certainly YouTube's current anti-bot / PO-token "
        "enforcement blocking this server (or this specific video being extra-restricted), "
        "not a problem with your input. It's a known, actively unresolved issue for yt-dlp "
        "in general right now - see https://github.com/yt-dlp/yt-dlp/issues/12482. "
        f"Last underlying error: {last_error}"
    )
