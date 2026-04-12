# CAPA Intelligence — Streamlit + OpenRouter Demo
> Claude Code project memory. Read this at the start of every session.

---

## Project purpose

Build a live demo of an AI-powered CAPA (Corrective & Preventive Action) and Root Cause Analysis assistant for pharma GxP environments. The app is built with **Streamlit**, calls LLMs via **OpenRouter**, and produces a tamper-evident audit trail suitable for 21 CFR Part 11 / Annex 11 compliance.

This is a **demo app** — prioritise clarity, live streaming effects, and model-switching wow moments over production hardening.

---

## Project structure

```
capa-demo/
├── CLAUDE.md                  ← you are here
├── .env                       ← OPENROUTER_API_KEY (never commit)
├── .env.example               ← safe to commit
├── requirements.txt
├── app.py                     ← Streamlit UI entry point
├── agent.py                   ← OpenRouter calls, streaming RCA logic
├── prompts.py                 ← all system prompts and few-shot examples
├── audit.py                   ← audit trail: lock, hash, export
├── models.py                  ← OpenRouter model registry
├── .claude/
│   ├── commands/
│   │   ├── scaffold.md        ← /scaffold — bootstrap a new file
│   │   ├── run-demo.md        ← /run-demo — launch Streamlit
│   │   └── add-incident.md    ← /add-incident — add a new sample incident
│   └── skills/
│       └── rca-prompt/
│           └── SKILL.md       ← RCA prompt engineering guidance
└── sample_incidents/
    ├── yield_deviation.txt
    ├── endotoxin_oos.txt
    └── cold_chain_excursion.txt
```

---

## Key commands

| Command | What it does |
|---|---|
| `streamlit run app.py` | Launch the demo app |
| `pip install -r requirements.txt` | Install all dependencies |
| `/scaffold <filename>` | Create a new module with correct imports |
| `/run-demo` | Start Streamlit and open browser |
| `/add-incident <name>` | Scaffold a new sample incident text file |

---

## Tech stack

- **Python 3.11+**
- **Streamlit** — UI framework; use `st.write_stream()` for token streaming
- **OpenAI SDK** — used as OpenRouter client (base_url override)
- **OpenRouter** — multi-model gateway; base URL: `https://openrouter.ai/api/v1`
- **python-dotenv** — load `.env` secrets
- **hashlib** — SHA-256 record locking for audit trail

---

## Environment variables

```bash
# .env — never commit this file
OPENROUTER_API_KEY=sk-or-...

# Optional
APP_TITLE="CAPA Intelligence"
DEFAULT_MODEL=anthropic/claude-sonnet-4-5
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## OpenRouter setup

OpenRouter is API-compatible with the OpenAI SDK. Initialise the client like this:

```python
# agent.py
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
```

**No other changes needed** — all `client.chat.completions.create()` calls work identically.

---

## Supported models (models.py)

```python
MODELS = {
    "Claude Sonnet (Anthropic)": "anthropic/claude-sonnet-4-5",
    "GPT-4o (OpenAI)":           "openai/gpt-4o",
    "Gemini Pro (Google)":       "google/gemini-pro",
}
```

The demo switches models via a `st.sidebar.selectbox` — no code changes required, just pass `model=selected_model` to the API call.

---

## Core agent function

```python
# agent.py — streaming RCA generator
def run_rca(incident_text: str, model: str):
    """Yields text chunks from the RCA reasoning stream."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": RCA_SYSTEM_PROMPT},
            {"role": "user",   "content": incident_text},
        ],
        stream=True,
        extra_headers={
            "HTTP-Referer": "https://emb.ai",     # shown in OpenRouter dashboard
            "X-Title":      "CAPA Intelligence",
        },
    )
    for chunk in response:
        yield chunk.choices[0].delta.content or ""
```

---

## RCA system prompt (in prompts.py)

The system prompt must instruct the model to:

1. Output a structured 5-Why chain with **Why 1** through **Why 5** as markdown headers
2. For each Why, cite the evidence source in italics (e.g. *Batch record BLR-2024-0882*)
3. End with a **Root Cause** section clearly labelled
4. Then output a **CAPA Actions** section with two sub-lists: Corrective and Preventive
5. Each action must include: action text, owner role, due date (relative, e.g. "within 7 days"), and effectiveness check date
6. Respond in plain markdown — no JSON wrappers

Example few-shot structure to include in the prompt:

```
## Why 1
Batch yield fell 13.8% below specification.
*Evidence: MES batch record BLR-IG-2024-0882*

## Why 2
...

## Root Cause
Change control closure checklist did not include verification that
cascade pH-DO control was re-enabled post-maintenance.

## CAPA Actions
### Corrective
- Quarantine batch BLR-IG-2024-0882 | Owner: QA Manager | Due: 24 hours
...
### Preventive
- Update SOP BCN-MFG-041 | Owner: Process Engineering | Due: 30 days
...
```

---

## Streamlit UI structure (app.py)

```
Sidebar
  └── Model selector (selectbox from MODELS dict)
  └── Site selector (text input or selectbox)
  └── Product (text input)
  └── Incident ID (auto-generated or manual)

Main area
  ├── Incident description (st.text_area, ~200 chars placeholder)
  ├── [Run RCA Agent] button
  ├── Streaming output panel (st.write_stream or st.empty + placeholder)
  ├── [Generate CAPA Plan] button (appears after RCA completes)
  ├── CAPA output panel
  └── Audit Trail expander
        └── Table of all runs this session (timestamp, model, incident ID, hash)
        └── [Download CAPA Record (.json)] button
```

Use `st.session_state` to persist:
- `audit_trail: list[dict]` — all records this session
- `last_rca: str` — last RCA output (passed into CAPA generation)
- `incident_id: str` — current incident ID

---

## Audit trail & record locking (audit.py)

Every completed RCA+CAPA run must produce a locked record:

```python
import hashlib, json
from datetime import datetime, timezone

def lock_record(incident_id, site, product, model, rca_text, capa_text, user="demo"):
    record = {
        "incident_id":   incident_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "site":          site,
        "product":       product,
        "model":         model,
        "user":          user,
        "rca_output":    rca_text,
        "capa_output":   capa_text,
    }
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    record["sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    record["locked"] = True
    return record
```

The `sha256` field proves the record has not been altered post-generation — this is the 21 CFR Part 11 integrity hook to highlight in the demo.

---

## Demo script (talking points)

### Phase 1 — Setup (5 min)
- Open terminal, run `claude` in the project folder
- Show `CLAUDE.md` being read on session start
- Type: *"Scaffold the project structure"* — watch Claude create all files

### Phase 2 — OpenRouter wiring (8 min)
- Show `.env` and `models.py`
- Type: *"Wire up the OpenRouter client in agent.py with streaming support"*
- Show the 3-model dropdown in the sidebar — no code change to switch

### Phase 3 — Streamlit UI (10 min)
- Type: *"Build the full Streamlit UI in app.py per the CLAUDE.md spec"*
- Run `streamlit run app.py`
- Paste a sample incident → hit Run RCA Agent → watch tokens stream live
- **Wow moment**: switch model in sidebar, run again, compare reasoning

### Phase 4 — Audit trail (7 min)
- Type: *"Add the audit trail and download button per CLAUDE.md"*
- Show the SHA-256 hash in the downloaded JSON
- Mention 21 CFR Part 11 / Annex 11 — the hash + timestamp + model field = full provenance

### Phase 5 — Live audience edit (5 min)
- Ask audience for a feature request
- Type it as a one-line Claude Code prompt
- Show the edit applied in < 30 seconds
- Suggested prompt: *"Add a confidence score (High / Medium / Low) to each Why step"*

---

## Sample incidents (sample_incidents/)

Three pre-written incident descriptions ready to paste into the demo:

- `yield_deviation.txt` — Insulin Glargine biosimilar, Bengaluru Plant 3, −13.8% yield
- `endotoxin_oos.txt` — Trastuzumab DS, Hyderabad, endotoxin 4.8× above limit
- `cold_chain_excursion.txt` — Pegfilgrastim FDP, Mumbai depot, +9.2°C for 4h 17min

---

## Custom slash commands (.claude/commands/)

### /run-demo
```markdown
Start the Streamlit app for the CAPA demo.
Run: streamlit run app.py
If port 8501 is busy, use --server.port 8502.
Open the browser URL shown in the terminal output.
```

### /scaffold
```markdown
Create the file $ARGUMENTS with correct imports for this project.
Follow the structure in CLAUDE.md. Add a module docstring.
Do not add placeholder logic — leave functions as `pass` with a TODO comment.
```

### /add-incident
```markdown
Create sample_incidents/$ARGUMENTS.txt with a realistic pharma manufacturing
incident description (3–5 sentences). Include: product name, site, batch ID,
deviation type, and initial observation. Use biosimilar or small molecule API context.
```

---

## Conventions

- All timestamps in **UTC ISO 8601** format
- Incident IDs: `INC-{SITE}-{YYYY}-{4-digit-seq}` e.g. `INC-BLR-2024-0471`
- Model strings always use the full OpenRouter path e.g. `anthropic/claude-sonnet-4-5`
- Never log or print the `OPENROUTER_API_KEY`
- Keep `prompts.py` as the **single source of truth** for all prompt text — no inline prompts in `app.py` or `agent.py`

---

## Done-definition for this demo

- [ ] `streamlit run app.py` launches without errors
- [ ] Incident text → RCA streams token-by-token in the UI
- [ ] Model can be switched mid-session with no code changes
- [ ] CAPA plan generates from the RCA output
- [ ] Audit trail table shows all runs with timestamp + model + hash
- [ ] JSON download works and contains `sha256` field
- [ ] All three sample incidents produce coherent output
