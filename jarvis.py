import flet as ft
import requests

# ===================== OLLAMA CONFIG =====================

# If running Ollama on the same machine:
#   ollama serve        # usually auto-starts when you run any ollama command
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
        return f"J.A.R.V.I.S.: Error talking to the local model: {e}"


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

    # Conversation history (for the model)
    conversation = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., a precise, technical AI assistant. "
                "You help with coding, Linux, networking, and general questions. "
                "Be clear and concise."
            ),
        }
    ]

    def add_message(text: str, is_user: bool):
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

        # Add to conversation history
        conversation.append({"role": "user", "content": user_text})

        # Disable input while thinking
        input_box.disabled = True
        send_button.disabled = True
        page.update()

        # Call local Ollama
        reply = call_model_api(conversation)

        # Update history and UI with assistant reply
        conversation.append({"role": "assistant", "content": reply})
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
