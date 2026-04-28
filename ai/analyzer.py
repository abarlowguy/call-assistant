import json
import re
import anthropic
from ai.prompts import build_system_prompt
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TRANSCRIPT_HISTORY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class Analyzer:
    def __init__(self, on_insight, on_search_request):
        """
        on_insight(text: str) — called with each AI suggestion/insight
        on_search_request(query: str) — called when AI wants a web search
        """
        self.on_insight = on_insight
        self.on_search_request = on_search_request
        self._transcript_history = []
        self._project_context = None

    def set_project_context(self, context: str | None):
        self._project_context = context
        self._transcript_history.clear()

    def add_transcript(self, text: str):
        self._transcript_history.append(text)
        if len(self._transcript_history) > MAX_TRANSCRIPT_HISTORY:
            self._transcript_history = self._transcript_history[-MAX_TRANSCRIPT_HISTORY:]
        self._analyze()

    def _analyze(self):
        transcript_block = "\n".join(self._transcript_history[-10:])
        system = build_system_prompt(self._project_context)
        user_msg = f"LIVE TRANSCRIPT (most recent):\n{transcript_block}\n\nWhat should I know or ask right now?"

        accumulated = ""
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": user_msg}]
        ) as stream:
            for text in stream.text_stream:
                accumulated += text

        search_match = re.search(r'\{"web_search":\s*"([^"]+)"\}', accumulated)
        if search_match:
            query = search_match.group(1)
            self.on_search_request(query)
            accumulated = re.sub(r'\{"web_search":\s*"[^"]+"\}', '', accumulated).strip()

        if accumulated:
            self.on_insight(accumulated)
