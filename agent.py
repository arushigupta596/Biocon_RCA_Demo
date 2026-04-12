"""OpenRouter calls and streaming RCA/CAPA logic for CAPA Intelligence."""

import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import RCA_SYSTEM_PROMPT, CAPA_SYSTEM_PROMPT

load_dotenv()

try:
    import streamlit as st
    _api_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
except Exception:
    _api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_api_key,
)

_EXTRA_HEADERS = {
    "HTTP-Referer": "https://emb.ai",
    "X-Title":      "CAPA Intelligence",
}


def run_rca(incident_text: str, model: str):
    """Yields text chunks from the RCA reasoning stream."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RCA_SYSTEM_PROMPT},
            {"role": "user",   "content": incident_text},
        ],
        stream=True,
        extra_headers=_EXTRA_HEADERS,
    )
    for chunk in response:
        yield chunk.choices[0].delta.content or ""


def run_capa(rca_text: str, incident_id: str, model: str):
    """Yields text chunks for a detailed CAPA plan based on the completed RCA."""
    user_message = (
        f"Incident ID: {incident_id}\n\n"
        f"RCA Report:\n{rca_text}\n\n"
        "Please produce the detailed CAPA Action Plan."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CAPA_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        stream=True,
        extra_headers=_EXTRA_HEADERS,
    )
    for chunk in response:
        yield chunk.choices[0].delta.content or ""
