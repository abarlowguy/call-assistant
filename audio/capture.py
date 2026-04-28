import sounddevice as sd
import numpy as np
import threading
import queue
from config import SAMPLE_RATE, CHANNELS, BLACKHOLE_DEVICE_NAME

def list_audio_devices():
    devices = sd.query_devices()
    result = []
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            result.append({"id": i, "name": d['name'], "channels": d['max_input_channels']})
    return result

def find_device_id(name_fragment: str) -> int | None:
    for d in list_audio_devices():
        if name_fragment.lower() in d['name'].lower():
            return d['id']
    return None

class AudioCapture:
    def __init__(self, mic_device_id: int | None, system_device_id: int | None, callback):
        self.mic_device_id = mic_device_id
        self.system_device_id = system_device_id
        self.callback = callback  # called with (numpy float32 array, source: str)
        self._mic_stream = None
        self._system_stream = None
        self._running = False

    def _mic_handler(self, indata, frames, time, status):
        if self._running:
            self.callback(indata[:, 0].copy(), source="mic")

    def _system_handler(self, indata, frames, time, status):
        if self._running:
            self.callback(indata[:, 0].copy(), source="system")

    def start(self):
        self._running = True
        if self.mic_device_id is not None:
            self._mic_stream = sd.InputStream(
                device=self.mic_device_id,
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                dtype='float32',
                callback=self._mic_handler
            )
            self._mic_stream.start()
        if self.system_device_id is not None:
            self._system_stream = sd.InputStream(
                device=self.system_device_id,
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                dtype='float32',
                callback=self._system_handler
            )
            self._system_stream.start()

    def stop(self):
        self._running = False
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
        if self._system_stream:
            self._system_stream.stop()
            self._system_stream.close()
