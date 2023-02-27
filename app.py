from os import environ
from ast import Assign
from multiprocessing.util import ForkAwareThreadLock
from unittest.mock import NonCallableMagicMock
from db import db, User
from flask import Flask, request
import json
import datetime
from flask_cors import CORS, cross_origin
import users_dao


app = Flask(__name__)
cors = CORS(app)
db_filename = "contruction.db"

app.config['CORS_HEADERS'] = 'Content-Type'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config['SECRET_KEY'] = 'mysecret'

db.init_app(app)
with app.app_context():
    db.create_all()

def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("Missing Authorization header.", 400)
 
    #Header looks like Authorization: Bearer fkafpkakfpow
    bearer_token = auth_header.replace("Bearer ", "").strip()
    if bearer_token is None or not bearer_token:
        return False, failure_response("Invalid authorization header", 400)
 
    return True, bearer_token

def success_response(data, code=200):
    """
    Returns a generic success response
    """
    return json.dumps(data), code

 
def failure_response(message, code=404):
    """
    Returns a generic failure response
    """
    return json.dumps({"error": message}), code

@app.route("/")
def hello_world():
    """
    Endpoint for printing Hello World!
    """
    return "Hello World!"

@app.route("/api/user/")
def get_users():
    """
    Endpoint for the getting all users
    """
    user = [user.serialize() for user in User.query.all()]
    return success_response({"user": user})

@app.route("/api/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
    first = body.get("first")
    last = body.get("last")
 
    if email is None or password is None or first is None or last is None:
        return failure_response("Missing first name, last name, email, password, or phone number", 400)
 
    success, user = users_dao.create_user(email, password, first, last)

    if not success:
        return failure_response("User already exists", 400)
    
    user_serialize = user.serialize()

    return success_response(user_serialize, 201)

@app.route("/api/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
 
    if email is None or password is None:
        return failure_response("Missing password or email", 400)
 
    success, user = users_dao.verify_credentials(email, password)
 
    if not success:
        return failure_response("Incorrect email or password", 401)
    user.renew_session()
    user_serialize = user.serialize()
    db.session.commit()
    return success_response(user_serialize)
 
 
@app.route("/api/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)
    success_user, user = users_dao.renew_session(update_token)
 
    if not success_user:
        return failure_response("Invalid update token", 400)
   
    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )

@app.route("/api/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message
 
    In your project, you will use the same logic for any endpoint that needs
    authentication
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response("Could not extract session token", 400)
   
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Session token Invalid", 400)
 
    return success_response({"message": "You have successfully implemented sessions!"})
 
 
@app.route("/api/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, session_token = extract_token(request)
 
    if not success:
        return failure_response("Could not extract session token", 400)
 
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
 
    user.session_token = ""
    user.session_expiration = datetime.datetime.now()
    user.update_token = ""

    db.session.commit()
 
    return success_response({"message": "You have successfully logged out"})

@app.route("/api/user/<int:user_id>/", methods = ["POST"])
def update_user(user_id):
    """
    Endpoint for updating a user
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    body = json.loads(request.data)
    first = body.get("first")
    last = body.get("last")
    email = body.get("email")
    phone_number = body.get("phone_number")
    if first is None or last is None or email is None or phone_number is None:
        return failure_response("Missing first name, last name, email, or phone number", 400)
    user.first = first 
    user.last = last 
    user.email = email 
    user.phone_number = phone_number 
    db.session.commit()
    return success_response(user.serialize(), 200)

@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())

@app.route("/api/user/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """
    Endpoint for deleting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/api/user/<int:user_id>/password/", methods = ["POST"])
def change_password(user_id):
    """
    Endpoint for changing a user password
    """
    user = User.query.filter_by(id = user_id).first()
    body = json.loads(request.data)
    new_pass = body.get("new_password")
    old_pass = body.get("old_password")

    if new_pass is None or old_pass is None:
        return failure_response("Missing old or new password", 400)
    response, user = user.change_password(old_password = old_pass, new_password = new_pass)
    db.session.commit()
    return success_response(user)




if __name__ == "__main__":
    app.run( host="0.0.0.0", port=8000, debug=True)