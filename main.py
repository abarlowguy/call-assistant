import threading
import time
import uvicorn
import webview

def start_server():
    uvicorn.run("api.server:app", host="127.0.0.1", port=8765, log_level="warning")

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)  # wait for uvicorn to bind

    webview.create_window(
        "Call Assistant",
        "http://127.0.0.1:8765",
        width=1100,
        height=700,
        resizable=True
    )
    webview.start()
