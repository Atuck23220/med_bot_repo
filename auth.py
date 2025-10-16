import os
import json
import hashlib

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password, confirm_password):
    users = load_users()
    if not email.endswith("@vcu.edu"):
        return "ERROR: Must use a @vcu.edu email address."
    if email in users:
        return "ERROR: User already exists. Please log in."
    if password != confirm_password:
        return "ERROR: Passwords do not match."

    users[email] = hash_password(password)
    save_users(users)
    return "SUCCESS: Account created successfully. Please log in."

def login_user(email, password):
    users = load_users()
    if email not in users:
        return "ERROR: User not found. Please register."
    if users[email] != hash_password(password):
        return "ERROR: Invalid password. Please try again."
    return "SUCCESS: Login successful. You may now continue to the chat."
