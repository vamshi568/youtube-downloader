"""
Best-effort bootstrap for a local PO (Proof-of-Origin) Token provider.

YouTube now requires a PO token for most non-SABR format URLs (see
https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide). Manually extracting one
per-video isn't practical for a public downloader, so instead we run a small
local HTTP server that generates tokens automatically, and install the
official yt-dlp plugin (`bgutil-ytdlp-pot-provider`, added to requirements.txt)
which talks to it on http://127.0.0.1:4416 automatically - no extra yt-dlp
config needed once the server is up.

The actual token-generation server binary comes from
https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs (a Rust
re-implementation of https://github.com/Brainicism/bgutil-ytdlp-pot-provider
that ships a single prebuilt binary, which is much easier to run on
Streamlit Community Cloud than the original Node/TypeScript server that
needs an `npm ci && npx tsc` build step).

Everything here is defensive on purpose: this is a third-party binary
downloaded at runtime on a free, shared hosting platform, so if anything
about this goes wrong (network blocked, asset renamed upstream, binary
doesn't run in this container, port already in use by something else, etc.)
we log why and return False instead of crashing the app. The rest of the
app (downloader.py) is written to keep working - just without a PO token -
if this fails.
"""

import os
import socket
import subprocess
import time
import urllib.request

POT_SERVER_PORT = 4416
_BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
_BIN_PATH = os.path.join(_BIN_DIR, "bgutil-pot")
_DOWNLOAD_URL = (
    "https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/"
    "releases/latest/download/bgutil-pot-linux-x86_64"
)
_MIN_EXPECTED_BYTES = 1_000_000  # sanity check that we didn't download an HTML error page

_server_process = None  # keeps the subprocess alive for the life of this Python process


def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _download_binary() -> bool:
    os.makedirs(_BIN_DIR, exist_ok=True)
    if os.path.exists(_BIN_PATH) and os.path.getsize(_BIN_PATH) > _MIN_EXPECTED_BYTES:
        return True
    try:
        print(f"DEBUG: [pot_server] Downloading PO-token server binary from {_DOWNLOAD_URL}")
        tmp_path = _BIN_PATH + ".part"
        urllib.request.urlretrieve(_DOWNLOAD_URL, tmp_path)
        size = os.path.getsize(tmp_path)
        if size < _MIN_EXPECTED_BYTES:
            print(f"DEBUG: [pot_server] Downloaded file looks wrong (only {size} bytes) - aborting")
            os.remove(tmp_path)
            return False
        os.replace(tmp_path, _BIN_PATH)
        os.chmod(_BIN_PATH, 0o755)
        print(f"DEBUG: [pot_server] Downloaded binary OK ({size} bytes)")
        return True
    except Exception as e:
        print(f"DEBUG: [pot_server] Failed to download PO-token server binary: {e}")
        return False


def ensure_pot_server_running(startup_timeout: float = 8.0) -> bool:
    """
    Best-effort: download + launch the local PO-token HTTP server if it
    isn't already running. Never raises. Returns True if a server is
    confirmed reachable on 127.0.0.1:4416, False otherwise (caller should
    just proceed without a PO token in that case).
    """
    global _server_process
    try:
        if _is_port_open("127.0.0.1", POT_SERVER_PORT):
            return True  # already running from a previous Streamlit rerun

        already_started_by_us = _server_process is not None and _server_process.poll() is None
        if not already_started_by_us:
            if not _download_binary():
                return False
            print("DEBUG: [pot_server] Starting local PO-token server...")
            try:
                _server_process = subprocess.Popen(
                    [_BIN_PATH, "server", "--port", str(POT_SERVER_PORT)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                print(f"DEBUG: [pot_server] Failed to launch server binary: {e}")
                return False

        deadline = time.time() + startup_timeout
        while time.time() < deadline:
            if _is_port_open("127.0.0.1", POT_SERVER_PORT):
                print("DEBUG: [pot_server] PO-token server is up.")
                return True
            time.sleep(0.5)

        print("DEBUG: [pot_server] PO-token server did not come up in time.")
        return False
    except Exception as e:
        print(f"DEBUG: [pot_server] ensure_pot_server_running failed unexpectedly: {e}")
        return False
