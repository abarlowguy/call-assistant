#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
export TAVILY_API_KEY="${TAVILY_API_KEY:-}"
python main.py
