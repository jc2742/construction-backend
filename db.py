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
    email = db.Column(db.String, nullable = False)

    def __init__(self, **kwargs):
        self.first = kwargs.get("first")
        self.last = kwargs.get("last")
        self.email = kwargs.get("email")
    
    def serialize(self):
        """
        Serializes an User object
        """
        return {
            "id" : self.id,
            "first" : self.first,
            "last" : self.last,
            "email": self.email
        }