"""Tests for MedBot's rule-based safety pipeline (app.chatbot_interface).

These never call the OpenAI API: a dummy key satisfies app.py's import-time
check, and openai_generate is replaced with a stub in every test.
"""
import os

# Must be set before importing app, which raises ValueError without a key.
# Overwrite (not setdefault) so a real key in the shell is never used.
os.environ["OPENAI_API_KEY"] = "test-dummy-key"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import pytest

import app

EMERGENCY_MSG = "Call 911 or seek immediate medical help"
CRISIS_MSG = "CRISIS DETECTED"
GROUNDING_MSG = "Try grounding techniques"
GLAD_MSG = "glad to hear the grounding techniques are helping"
NOT_HELPING_MSG = "grounding strategies"
DOSING_MSG = "Dosing/prescription request detected"
COUNSELING_URL = "counseling.vcu.edu"
STUB_REPLY = "STUB LLM REPLY"


# ---- Fixtures ----

@pytest.fixture(autouse=True)
def llm_calls(monkeypatch):
    """Replace the OpenAI call with a stub and record what it was asked."""
    calls = []

    def fake_generate(system_prompt, user_text):
        calls.append((system_prompt, user_text))
        return STUB_REPLY

    monkeypatch.setattr(app, "openai_generate", fake_generate)
    return calls


@pytest.fixture(autouse=True)
def logged_in(monkeypatch):
    monkeypatch.setitem(app.session_state, "logged_in", True)
    monkeypatch.setitem(app.session_state, "user", "test@vcu.edu")


def send(message, history=None):
    """Send one message; return (bot reply text, updated history)."""
    history, _ = app.chatbot_interface(message, list(history or []))
    return history[-1]["content"], history


@pytest.fixture
def grounding_history():
    """A history whose last bot message is the grounding-techniques prompt."""
    reply, history = send("I'm feeling really overwhelmed")
    assert GROUNDING_MSG in reply
    return history


# ---- Fresh conversation (expected to pass) ----

def test_requires_login(monkeypatch, llm_calls):
    monkeypatch.setitem(app.session_state, "logged_in", False)
    reply, _ = send("hello")
    assert reply == "ERROR: Please log in first."
    assert llm_calls == []


def test_chest_pain_returns_emergency(llm_calls):
    reply, _ = send("I'm having chest pain")
    assert EMERGENCY_MSG in reply
    assert llm_calls == []


def test_overdose_returns_emergency(llm_calls):
    reply, _ = send("I took an overdose")
    assert EMERGENCY_MSG in reply
    assert llm_calls == []


def test_suicidal_statement_returns_crisis(llm_calls):
    reply, _ = send("I want to kill myself")
    assert CRISIS_MSG in reply
    assert "988" in reply
    assert llm_calls == []


def test_distress_words_trigger_grounding_prompt(llm_calls):
    reply, _ = send("I'm so stressed about exams")
    assert GROUNDING_MSG in reply
    assert llm_calls == []


def test_dosing_request_is_blocked(llm_calls):
    reply, _ = send("What dose of ibuprofen should I take?")
    assert DOSING_MSG in reply
    assert llm_calls == []


def test_medical_question_uses_medical_prompt(llm_calls):
    reply, _ = send("What are common side effects of statins?")
    assert reply == STUB_REPLY
    assert llm_calls[0][0] == app.SYS_MEDICAL


def test_general_question_uses_general_prompt(llm_calls):
    reply, _ = send("What's the capital of France?")
    assert reply == STUB_REPLY
    assert llm_calls[0][0] == app.SYS_GENERAL


# ---- After a grounding prompt (expected to pass) ----

def test_after_grounding_suicidal_statement_returns_crisis(grounding_history):
    reply, _ = send("I want to kill myself", grounding_history)
    assert CRISIS_MSG in reply


def test_after_grounding_not_working_refers_to_counseling(grounding_history):
    reply, _ = send("it's not working", grounding_history)
    assert NOT_HELPING_MSG in reply
    assert GLAD_MSG not in reply


def test_after_grounding_feeling_better_is_acknowledged(grounding_history):
    reply, _ = send("that helped, I feel better", grounding_history)
    assert GLAD_MSG in reply


# ---- After a grounding prompt: known bugs (expected to FAIL before the fix) ----

def test_after_grounding_chest_pain_returns_emergency(grounding_history, llm_calls):
    reply, _ = send("I'm having chest pain", grounding_history)
    assert EMERGENCY_MSG in reply
    assert COUNSELING_URL not in reply
    assert llm_calls == []


def test_after_grounding_overdose_returns_emergency_or_crisis(grounding_history, llm_calls):
    reply, _ = send("I took an overdose", grounding_history)
    assert EMERGENCY_MSG in reply or CRISIS_MSG in reply
    assert llm_calls == []


def test_after_grounding_isnt_working_is_not_treated_as_helping(grounding_history):
    reply, _ = send("it isn't working", grounding_history)
    assert GLAD_MSG not in reply
    assert COUNSELING_URL in reply
