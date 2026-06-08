"""
mdConvertor — main.py
Entry point: starts Flask in a background thread, then opens a native
PyWebView window pointed at the local Flask server.
"""
import threading
import socket
import time
import sys
import os
import webview

# ── Path helpers (works both in dev and inside PyInstaller bundle) ────────────
def resource_path(relative_path: str) -> str:
    """Return absolute path to resource, works for dev and PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def find_free_port() -> int:
    """Bind to port 0 and let the OS pick a free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Block until the Flask server is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Flask server did not start on port {port} within {timeout}s")


def start_flask(port: int) -> None:
    """Import and run the Flask app (import here so MEIPASS is set first)."""
    # Patch template/static folder paths before importing server
    os.environ["MDCONVERTOR_TEMPLATE_DIR"] = resource_path("templates")
    from server import app
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def main() -> None:
    port = find_free_port()

    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()

    # Wait until Flask is ready before creating the window
    wait_for_server(port)

    window = webview.create_window(
        title="mdConvertor",
        url=f"http://127.0.0.1:{port}",
        width=1200,
        height=820,
        min_size=(900, 600),
        background_color="#0a0a0f",
    )

    if sys.platform == "darwin":
        storage_dir = os.path.expanduser("~/Library/Application Support/mdConvertor")
    elif sys.platform == "win32":
        storage_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "mdConvertor")
    else:
        storage_dir = os.path.expanduser("~/.config/mdConvertor")

    os.makedirs(storage_dir, exist_ok=True)
    webview.start(debug=False, private_mode=False, storage_path=storage_dir)


if __name__ == "__main__":
    main()
