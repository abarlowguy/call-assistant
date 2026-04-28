import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

WHISPER_MODEL = "base.en"
WHISPER_DEVICE = "cpu"
CHUNK_SECONDS = 3
SAMPLE_RATE = 16000
CHANNELS = 1

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TRANSCRIPT_HISTORY = 50

BLACKHOLE_DEVICE_NAME = "BlackHole 2ch"


def validate_keys():
    missing = [k for k, v in [("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY), ("TAVILY_API_KEY", TAVILY_API_KEY)] if not v]
    if missing:
        print(f"Warning: {', '.join(missing)} not set. Set them before starting the server.")
