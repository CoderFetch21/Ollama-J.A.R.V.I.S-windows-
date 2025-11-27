# -*- coding: utf-8 -*-

import os
import json
import requests
import flet as ft

# ===================== MEMORY CONFIG =====================

MEMORY_FILE = "jarvis_memory.json"
MAX_MEMORY_MESSAGES = 60  # keep the last N messages in memory


def load_memory():
    """Load conversation history from disk, if present."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_memory(conversation):
    """Save conversation history to disk (trimmed)."""
    try:
        trimmed = conversation[-MAX_MEMORY_MESSAGES:]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=2)
    except Exception:
        # Do not crash the app if saving fails
        pass


# ===================== OLLAMA CONFIG =====================

# Make sure Ollama is running and you have:
#   ollama pull llama3.2
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"


def call_model_api(messages):
    """
    Call local Ollama chat API.
    messages: list of {"role": "...", "content": "..."}
    Returns a string reply.
    """
    body = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
    }

    try:
        resp = requests.post(OLLAMA_URL, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Expected shape:
        # {
        #   "message": { "role": "assistant", "content": "..." },
        #   ...
        # }
        msg = data.get("message", {})
        content = msg.get("content", "")
        if content:
            return content

        return "J.A.R.V.I.S.: Local model returned an empty or unexpected response."

    except Exception as e:
        return "J.A.R.V.I.S.: Error talking to the local model: {0}".format(e)


# ===================== FLET UI (WINDOW) =====================

def main(page: ft.Page):
    # Window / tab setup
    page.title = "J.A.R.V.I.S."
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10

    # Title at the top
    title = ft.Text(
        "J.A.R.V.I.S.",
        size=24,
        weight=ft.FontWeight.BOLD,
    )

    # ListView to hold chat bubbles
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # Text input for user
    input_box = ft.TextField(
        hint_text="Ask J.A.R.V.I.S. anything...",
        expand=True,
        autofocus=True,
    )

    # Send button
    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
    )

    # Base system message describing behavior
    base_system_message = {
        "role": "system",
        "content": (
            "You are J.A.R.V.I.S., a precise, technical AI assistant. "
            "You help with coding, Linux, networking, and general questions. "
            "Be clear and concise. You have a long-term memory file that may "
            "contain facts the user previously told you; you can use them when helpful."
        ),
    }

    # Load memory from disk
    loaded = load_memory()
    if not loaded:
        conversation = [base_system_message]
    else:
        if loaded[0].get("role") != "system":
            loaded.insert(0, base_system_message)
        conversation = loaded

    # Show any previous conversation in the UI (optional)
    for msg in conversation:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            color = ft.Colors.BLUE_300
            align = ft.MainAxisAlignment.END
        elif role == "assistant":
            color = ft.Colors.GREY_800
            align = ft.MainAxisAlignment.START
        else:
            # system messages are not shown as bubbles
            continue

        chat.controls.append(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(content),
                        bgcolor=color,
                        padding=10,
                        border_radius=8,
                        width=page.width * 0.75 if page.width else None,
                    )
                ],
                alignment=align,
            )
        )

    page.update()

    def add_message(text, is_user):
        """Add a chat bubble to the UI."""
        color = ft.Colors.BLUE_300 if is_user else ft.Colors.GREY_800
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START

        chat.controls.append(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(text),
                        bgcolor=color,
                        padding=10,
                        border_radius=8,
                        width=page.width * 0.75 if page.width else None,
                    )
                ],
                alignment=align,
            )
        )
        page.update()

    def handle_send(_):
        user_text = input_box.value.strip()
        if not user_text:
            return

        # Show user message
        add_message(user_text, is_user=True)
        input_box.value = ""
        page.update()

        # Add to conversation history and save
        conversation.append({"role": "user", "content": user_text})
        save_memory(conversation)

        # Disable input while thinking
        input_box.disabled = True
        send_button.disabled = True
        page.update()

        # Call local Ollama
        reply = call_model_api(conversation)

        # Update history, save, and show assistant reply
        conversation.append({"role": "assistant", "content": reply})
        save_memory(conversation)
        add_message(reply, is_user=False)

        # Re-enable input
        input_box.disabled = False
        send_button.disabled = False
        input_box.focus()
        page.update()

    # Wire events
    input_box.on_submit = handle_send
    send_button.on_click = handle_send

    # Layout the page
    page.add(
        ft.Column(
            controls=[
                title,
                ft.Divider(),
                chat,
                ft.Row(controls=[input_box, send_button]),
            ],
            expand=True,
        )
    )


# Entry point: opens a desktop window
ft.app(target=main, view=ft.AppView.FLET_APP)
