from flask_login import UserMixin
from . import db

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(200), unique=True)
	password = db.Column(db.String(50))
	bots = db.relationship('Bots')

class Bots(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	name = db.Column(db.String(50))
	status = db.Column(db.String(20))
	starting_capital = db.Column(db.Float)
	current_wallet = db.Column(db.Float)
	par1 = db.Column(db.String(15))
	par2 = db.Column(db.String(15))
	par = db.Column(db.String(15))

