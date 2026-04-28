import queue
import threading
import numpy as np
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_DEVICE, SAMPLE_RATE


class Transcriber:
    def __init__(self, on_transcript):
        """
        on_transcript(text: str) called for each transcribed chunk.
        """
        self.on_transcript = on_transcript
        self._model = None
        self._audio_queue = queue.Queue()
        self._thread = None
        self._running = False

    def load_model(self):
        self._model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")

    def start(self):
        if self._model is None:
            self.load_model()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._audio_queue.put(None)  # sentinel

    def feed(self, audio_chunk: np.ndarray):
        self._audio_queue.put(audio_chunk)

    def _run(self):
        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=1.0)
                if chunk is None:
                    break
                segments, _ = self._model.transcribe(
                    chunk,
                    language="en",
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 500}
                )
                text = " ".join(seg.text.strip() for seg in segments).strip()
                if text:
                    self.on_transcript(text)
            except queue.Empty:
                continue
