from flask_login import UserMixin
from . import db

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(150), unique=True)
	password = db.Column(db.String(20))

class Bots(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	