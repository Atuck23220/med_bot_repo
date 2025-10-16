# med_bot_repo
AI-Powered Chatbot
MedBot

MedBot is a lightweight Python Gradio application that routes user questions to medical or general assistants via a safety gate and generates responses using the OpenAI API.

Disclaimer: MedBot is for educational purposes only. It does not provide medical advice and is not a diagnostic tool.

Features

• Safety gate to distinguish medical vs. general intent
• Two response modes: conservative medical (education-only) and general assistant
• File-backed registration and login
• Environment-based configuration (dotenv)
• Gradio web UI with tabs for chat and resources

Requirements

• Python 3.11 or newer
• OpenAI API key

Installation

Clone the repository
git clone https://github.com/Atuck23220/med_bot_repo.git

cd med_bot_repo

Create and activate a virtual environment
macOS/Linux: python3 -m venv .venv; source .venv/bin/activate
Windows (PowerShell): python -m venv .venv; .venv\Scripts\Activate.ps1

Install dependencies
pip install -r requirements.txt

Configuration

MedBot reads dotenv variables from a file named med_storage placed in the repository root.

Expected keys:
OPENAI_API_KEY=your_openai_key
APP_ENV=development
LOG_LEVEL=INFO

The med_storage file is local to each environment and is not part of the tracked source.

To use a standard .env file instead, update the dotenv loader in app.py to load .env and place the same keys there.

Running

Start the application:
python app.py

Gradio prints a local URL such as http://127.0.0.1:7860
. Open the link in a browser.

Usage

Register or log in from the UI

Open the Chat tab

Enter a prompt
• General example: “Suggest a quick dinner idea.”
• Medical-like example: “I have chest pain and shortness of breath.”

Safety gate behavior: clinical or emergency-related terms route to medical mode. Medical responses are informational and conservative and include guidance to seek professional care.

Architecture

• app.py — Gradio UI, routing, system prompts, OpenAI calls
• auth.py — register_user and login_user helpers (file-backed demo auth)
• requirements.txt — Python dependencies
• LICENSE — MIT
• README.md — project documentation

Design notes: single entry point for ease of review; separate prompts for medical vs. general modes; environment variables for configuration.

Testing

Optional local test setup with pytest:
pip install pytest
pytest -q

Suggested first unit seam: a function such as classify_intent(text) → “medical” or “general” with coverage for common and edge cases.

Security and Privacy

• Secrets are provided via environment variables from a local dotenv file
• No persistence of sensitive user data in this demo
• Not intended for PHI/PII or regulated workloads

Limitations

• Rule-based safety gate may miss nuanced language or produce false positives
• No persistent database beyond demo authentication
• No provider abstraction layer for switching among LLM backends

Roadmap

• Classifier-based or ruleset-driven safety gate
• Unit tests and GitHub Actions CI
• Optional session history and export
• Optional Dockerfile for reproducible deployment

License

MIT License (see LICENSE)
