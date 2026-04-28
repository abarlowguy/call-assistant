import numpy as np
import queue
from config import SAMPLE_RATE, CHUNK_SECONDS


class AudioProcessor:
    """
    Accumulates raw audio samples from the capture callback.
    Every CHUNK_SECONDS of audio, puts a numpy float32 array onto the output queue.
    """

    def __init__(self, output_queue: queue.Queue):
        self.output_queue = output_queue
        self._buffer = np.array([], dtype=np.float32)
        self._chunk_size = SAMPLE_RATE * CHUNK_SECONDS

    def feed(self, samples: np.ndarray, source: str):
        self._buffer = np.concatenate([self._buffer, samples])
        while len(self._buffer) >= self._chunk_size:
            chunk = self._buffer[:self._chunk_size]
            self._buffer = self._buffer[self._chunk_size:]
            self.output_queue.put(chunk)

    def flush(self):
        if len(self._buffer) > 0:
            self.output_queue.put(self._buffer.copy())
            self._buffer = np.array([], dtype=np.float32)
