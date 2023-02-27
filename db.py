import datetime
import hashlib
import os
from os import environ

import bcrypt
from flask_sqlalchemy import SQLAlchemy
import base64
import boto3
import io
from io import BytesIO
from mimetypes import guess_type, guess_extension
from PIL import Image
import random

import string

db = SQLAlchemy()

class User(db.Model):
    """
    User model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    first = db.Column(db.String, nullable = False)
    last = db.Column(db.String, nullable = False)

    # User Auth information
    email = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)

    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, **kwargs):
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.first = kwargs.get("first")
        self.last = kwargs.get("last")
        self.email = kwargs.get("email")
        self.renew_session()
    
    def serialize(self):
        """
        Serializes an User object
        """
        return {
            "id" : self.id,
            "first" : self.first,
            "last" : self.last,
            "email": self.email,
            "token": self.session_token,
            "update_token":self.update_token,
            
        }

    def change_password(self, **kwargs):
        old_pass = kwargs.get("old_password").encode("utf8")
        if  bcrypt.checkpw(old_pass, self.password_digest):
            self.password_digest =  bcrypt.hashpw(kwargs.get("new_password").encode("utf8"), bcrypt.gensalt(rounds=13))
            return True, self.serialize()
        return False, None

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()
    
    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token
    
    