# MedBot

[![tests](https://github.com/Atuck23220/med_bot_repo/actions/workflows/tests.yml/badge.svg)](https://github.com/Atuck23220/med_bot_repo/actions/workflows/tests.yml)

A small, readable demonstration of a **layered guardrail and intent-routing architecture** that sits in front of a large language model. The medical assistant is the reference use case; the structure is the point. The safety and routing layers are deliberately simple and rule-based so the control flow stays legible and easy to retarget at other domains (wellness, clinical information, retrieval-augmented Q&A).

> **Disclaimer:** MedBot is for educational and demonstration purposes only. It does not provide medical advice and is not a diagnostic tool.

---

## The idea

Most of the interesting logic in a safety-conscious LLM app is *not* the model call. It is everything that happens before and around it: deciding what to refuse outright, what to handle without the model, what to route where, and what prompt to hand the model when you do call it.

MedBot makes that layer explicit. Every user message passes through a fixed sequence of deterministic checks *before* any model call, so the failure mode is conservative: an unhandled edge case falls through to progressively more general handling rather than straight to an unguarded model. Each check is a small, independent rule set, which means the same skeleton can be pointed at a different domain by swapping keyword sets and system prompts rather than rewriting the flow.

The keyword lists are intentionally minimal. They are the demonstration's extension point, not a claim to completeness.

---

## Request pipeline

Each message is evaluated top to bottom. The first layer that matches handles the message and returns; nothing below it runs.

1. **Authentication gate** — unauthenticated users are stopped before any processing.
2. **Crisis interception** — self-harm language returns 988 / 911 and campus counseling resources immediately, without a model call. Stateless and deterministic by design.
3. **Stateful distress follow-up** — if the previous turn offered grounding techniques, this turn is interpreted in that context: a "not working" reply escalates to a professional-referral message, while a positive reply acknowledges and closes. This is the one layer that reasons across turns.
4. **Distress entry** — first-time distress language (panic, anxiety, overwhelmed, stressed) offers a 5-4-3-2-1 grounding exercise and primes the follow-up layer above.
5. **Safety gate** — emergency terms return a 911 message; dosing and prescription terms return a "consult a licensed clinician" refusal. Neither reaches the model.
6. **Intent routing** — remaining messages are classified medical vs. general by keyword. Medical messages get a cautious, education-only system prompt; everything else gets the general assistant prompt. Only here is the OpenAI API called.

The ordering is the safety property: high-severity triggers are caught in the earliest layers and short-circuit the rest, so a crisis message never depends on the routing logic at the bottom.

---

## Retargeting the skeleton

The same pipeline supports other assistants by editing data, not structure:

- **Wellness assistant** — widen the distress and grounding layers, drop the medical routing branch.
- **Clinical-information assistant** — expand the medical keyword set and the conservative prompt; keep the dosing and emergency refusals.
- **Retrieval-augmented (RAG) assistant** — insert a retrieval step inside the routed branch before the model call, so grounded context is supplied only after a message clears the guardrails.

In each case the auth, crisis, and safety layers stay in place; only the keyword sets, prompts, and the routed branch change.

---

## Features

- Ordered, rule-based guardrail pipeline evaluated before any model call
- Stateful distress follow-up that reasons across two turns
- Two response modes: cautious, education-only medical and general assistant
- File-backed registration and login (VCU-email gated)
- Environment-based configuration via dotenv
- Gradio web UI with Login, Register, Chat, and Resources tabs

## Requirements

- Python 3.11 or newer
- An OpenAI API key

## Installation

```bash
git clone https://github.com/Atuck23220/med_bot_repo.git
cd med_bot_repo
python3 -m venv .venv && source .venv/bin/activate   # Windows: python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

MedBot loads dotenv variables from a file named `med_storage` in the repository root:

```
OPENAI_API_KEY=your_openai_key
APP_ENV=development
LOG_LEVEL=INFO
```

`med_storage` is local to each environment and is not tracked. To use a standard `.env` file instead, update the dotenv loader in `app.py`.

## Running

```bash
python app.py
```

Gradio prints a local URL such as `http://127.0.0.1:7860`. Open it in a browser, register or log in, then use the Chat tab.

Example prompts:
- General: "Suggest a quick dinner idea."
- Medical: "What are common side effects of antihistamines?"
- Distress (grounding flow): "I feel really overwhelmed."

---

## Architecture

- `app.py` — Gradio UI, the guardrail pipeline, routing, system prompts, and the OpenAI call
- `auth.py` — `register_user` / `login_user` helpers (file-backed demo auth)
- `requirements.txt` — dependencies
- `README.md` / `LICENSE` — documentation and MIT license

Design notes: a single entry point keeps the control flow reviewable; each guardrail is an isolated rule set; prompts and keyword sets are separated from the flow so the skeleton is retargetable.

---

## Limitations

These are properties of a teaching demo

- **Keyword matching is shallow.** The gates use case-insensitive substring matching, so they miss paraphrase and novel phrasing and can false-positive on substrings. A production version would replace them with a trained classifier.
- **The general fallback is unguarded.** Any message that clears every safety layer but matches no medical keyword is routed to the general-assistant prompt, which is not safety-tuned. This is a known gap; a conservative default prompt or a safety-aware general prompt would close it.
- **Authentication is demo-grade.** Passwords are stored as unsalted SHA-256 hashes in a local JSON file. This is not suitable for real credentials; production would use a salted, slow password hash and a real user store.
- **Public sharing is on.** `demo.launch(share=True)` exposes a temporary public URL. Disable for local-only use.
- **No persistence or PHI/PII handling.** Not intended for regulated workloads.

## Roadmap

- Classifier-based safety and routing to replace keyword matching
- Conservative default prompt on the unmatched routing path
- Salted password hashing and a real user store
- Unit tests (starting with `route()` and `safety_gate()`) and GitHub Actions CI
- Optional retrieval-augmented branch and provider abstraction for switching LLM backends
- Optional session history and export

## License

MIT License (see `LICENSE`).
