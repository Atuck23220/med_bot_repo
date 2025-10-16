import os, gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from auth import register_user, login_user   # auth.py handles authentication

# ---- Load API key ----
load_dotenv("med_storage")
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ERROR: OPENAI_API_KEY not found in med_storage")
client = OpenAI(api_key=api_key)

# ---- System prompts ----
SYS_GENERAL = "You are a helpful, concise assistant."
SYS_MEDICAL = (
    "You are a cautious medical information assistant for education only. "
    "Provide general information, avoid diagnosis, prescriptions, or dosing. "
    "When appropriate, advise consulting a licensed clinician."
)

# ---- Safety terms ----
EMERGENCY_TERMS = {"chest pain","shortness of breath","stroke","unconscious",
                   "suicidal","overdose","severe bleeding","anaphylaxis",
                   "cant breathe","can't breathe", "kill myself"}
DOSING_TERMS = {"dose","dosage","mg","milligram","prescribe","prescription","titrate"}
MEDICAL_KEYWORDS = {"side effect","contraindication","symptom","diagnosis","medication","drug",
                    "hypertension","diabetes","asthma","antibiotic","antihistamine","statin",
                    "interaction","blood pressure","fever","rash","allergy"}

# ---- Session state (tracks login) ----
session_state = {"logged_in": False, "user": None}

# ---- Safety + routing ----
def safety_gate(text: str) -> str | None:
    t = text.lower()
    if any(keyword in t for keyword in EMERGENCY_TERMS):
        return "ERROR: Emergency detected. Call 911 or seek immediate medical help."
    if any(keyword in t for keyword in DOSING_TERMS):
        return "ERROR: Dosing/prescription request detected. Consult a licensed clinician."
    return None

def route(text: str) -> str:
    return "medical" if any(keyword in text.lower() for keyword in MEDICAL_KEYWORDS) else "general"

# ---- OpenAI call ----
def openai_generate(system_prompt: str, user_text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    )
    return response.choices[0].message.content.strip()

# ---- Chatbot interface ----
def chatbot_interface(user_message, history=[]):
    if not session_state["logged_in"]:
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": "ERROR: Please log in first."}
        ]
        return history, history

    msg = user_message.lower()

    # --- Crisis detection ---
    if any(keyword in msg for keyword in ["suicide", "kill myself", "end my life", "can't go on"]):
        response = (
            "CRISIS DETECTED: Please call 911 or dial 988 (Suicide & Crisis Lifeline) immediately.\n"
            "You may also reach out to VCU Counseling Services: https://counseling.vcu.edu/"
        )
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
        return history, history

    # --- Therapy distress detection ---
    if history and "Try grounding techniques" in history[-1]["content"]:
        if "not working" in msg:
            response = (
                "It seems the grounding strategies aren’t helping. "
                "Please consider reaching out to a professional: https://counseling.vcu.edu/"
            )
        elif any(keyword in msg for keyword in ["working", "better", "helped"]):
            response = (
                "I’m glad to hear the grounding techniques are helping! "
                "Remember, you can always return to them whenever you feel overwhelmed."
            )
        else:
            response = (
                "It seems you're still feeling distressed. "
                "Please consider reaching out to a professional: https://counseling.vcu.edu/"
            )
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
        return history, history

    # Initial distress detection
    if any(keyword in msg for keyword in ["panic", "anxiety", "overwhelmed", "stressed"]):
        response = (
            "Therapy Mode: I notice words that suggest distress. "
            "Try grounding techniques: 5-4-3-2-1 method (5 things you see, 4 you touch, 3 you hear, "
            "2 you smell, 1 you taste). Take slow breaths while doing this."
        )
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
        return history, history

    # --- Safety gate ---
    blocked = safety_gate(user_message)
    if blocked:
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": blocked}
        ]
        return history, history

    # --- General/medical routing ---
    mode = route(user_message)
    system_prompt = SYS_MEDICAL if mode == "medical" else SYS_GENERAL
    reply = openai_generate(system_prompt, user_message)
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply}
    ]
    return history, history

# ---- Gradio UI ----
with gr.Blocks() as demo:
    gr.Markdown("# 🩺 MedBot – Authentication + Chat")

    # --- Login Tab ---
    with gr.Tab("Login"):
        login_email = gr.Textbox(label="VCU Email")
        login_password = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("Login")
        login_output = gr.Textbox(label="Status")

        def handle_login(email, password):
            result = login_user(email, password)
            if result.startswith("SUCCESS"):
                session_state["logged_in"] = True
                session_state["user"] = email
            return result

        login_button.click(handle_login, [login_email, login_password], login_output)

    # --- Register Tab ---
    with gr.Tab("Register"):
        reg_email = gr.Textbox(label="VCU Email")
        reg_password = gr.Textbox(label="Password", type="password")
        reg_confirm = gr.Textbox(label="Confirm Password", type="password")
        reg_button = gr.Button("Register")
        reg_output = gr.Textbox(label="Status")

        reg_button.click(register_user, [reg_email, reg_password, reg_confirm], reg_output)

    # --- Chat Tab ---
    with gr.Tab("Chat") as chat_tab:
        chatbot = gr.Chatbot(type="messages")
        msg = gr.Textbox(label="Your message")
        clear = gr.Button("Clear")

        state = gr.State([])

        msg.submit(chatbot_interface, [msg, state], [chatbot, state])
        clear.click(lambda: ([], []), None, [chatbot, state])
        logout_chat = gr.Button("Exit Chat / Logout")
        logout_status = gr.Textbox(label="Status")

    def handle_chat_logout():
        session_state["logged_in"] = False
        session_state["user"] = None
        return "SUCCESS: You have exited the chat. Please log in again."

    logout_chat.click(handle_chat_logout, [], logout_status)

    # --- Resources Tab ---
    with gr.Tab("Resources"):
        gr.Markdown("### VCU Resources\n- [Counseling Services](https://counseling.vcu.edu/)")

if __name__ == "__main__":
    demo.launch(share=True)
