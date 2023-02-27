from os import environ
from ast import Assign
from multiprocessing.util import ForkAwareThreadLock
from unittest.mock import NonCallableMagicMock
from db import db, User
from flask import Flask, request
import json
import datetime
from flask_cors import CORS, cross_origin


app = Flask(__name__)
cors = CORS(app)
db_filename = "tattoo.db"

app.config['CORS_HEADERS'] = 'Content-Type'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config['SECRET_KEY'] = 'mysecret'

db.init_app(app)
with app.app_context():
    db.create_all()

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