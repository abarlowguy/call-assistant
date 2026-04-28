import asyncio
import json
import queue
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from audio.capture import AudioCapture, list_audio_devices, find_device_id
from audio.processor import AudioProcessor
from stt.transcriber import Transcriber
from ai.analyzer import Analyzer
from search.web import search
from context.loader import load_context, vault_search
from config import BLACKHOLE_DEVICE_NAME

# --- session state ---
_ws_clients: list[WebSocket] = []
_capture: AudioCapture | None = None
_transcriber: Transcriber | None = None
_analyzer: Analyzer | None = None
_processor: AudioProcessor | None = None
_audio_queue: queue.Queue = queue.Queue()

_event_loop: asyncio.AbstractEventLoop | None = None


async def _broadcast(msg: dict):
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


def _send_to_clients(msg: dict):
    asyncio.run_coroutine_threadsafe(_broadcast(msg), _event_loop)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _event_loop
    _event_loop = asyncio.get_event_loop()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/ui", StaticFiles(directory="ui"), name="ui")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


@app.get("/devices")
def get_devices():
    return list_audio_devices()


class StartRequest(BaseModel):
    mic_device_id: int | None = None
    system_device_id: int | None = None
    project_file: str | None = None


@app.post("/start")
def start_capture(req: StartRequest):
    global _capture, _transcriber, _analyzer, _processor

    project_context = None
    if req.project_file:
        try:
            project_context = load_context(req.project_file)
        except FileNotFoundError as e:
            return {"error": str(e)}

    _processor = AudioProcessor(_audio_queue)

    def on_audio(samples, source):
        _processor.feed(samples, source)

    def on_transcript(text):
        _send_to_clients({"type": "transcript", "text": text})
        _analyzer.add_transcript(text)

    def on_insight(text):
        _send_to_clients({"type": "insight", "text": text})

    def on_search_request(query):
        result = search(query)
        _send_to_clients({"type": "search", "query": query, "result": result})

    _analyzer = Analyzer(on_insight=on_insight, on_search_request=on_search_request)
    _analyzer.set_project_context(project_context)

    _transcriber = Transcriber(on_transcript=on_transcript)
    _transcriber.start()

    def drain_queue():
        while _capture and _capture._running:
            try:
                chunk = _audio_queue.get(timeout=0.5)
                _transcriber.feed(chunk)
            except queue.Empty:
                continue

    threading.Thread(target=drain_queue, daemon=True).start()

    system_id = req.system_device_id or find_device_id(BLACKHOLE_DEVICE_NAME)
    _capture = AudioCapture(
        mic_device_id=req.mic_device_id,
        system_device_id=system_id,
        callback=on_audio,
    )
    _capture.start()
    return {"status": "started", "project_loaded": bool(project_context)}


@app.post("/stop")
def stop_capture():
    global _capture, _transcriber
    if _capture:
        _capture.stop()
        _capture = None
    if _transcriber:
        _transcriber.stop()
        _transcriber = None
    return {"status": "stopped"}


class VaultSearchRequest(BaseModel):
    query: str


@app.post("/vault/search")
def vault_search_endpoint(req: VaultSearchRequest):
    return vault_search(req.query)


@app.get("/")
def root():
    return FileResponse("ui/index.html")
