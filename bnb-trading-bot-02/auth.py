from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, APP

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']

		user_logged = User.query.filter_by(email=email).first()

		if user_logged:
			if check_password_hash(user_logged.password, password):
				login_user(user_logged)
				print(f"Usuario {user_logged.email} logeado")

				return redirect(url_for('views.index'))
			else:
				rta = "Incorrect password"
				flash(rta, category='error')
		else:
			rta = "Incorrect email"
			flash(rta, category='error')

		print(rta)

	return render_template('login.html', title=APP)

@auth.route('/logout')
@login_required
def logout():
	logout_user()

	return redirect(url_for('views.index'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'GET':
		return render_template('signup.html', title=APP)
	else:
		if request.form['password1'] == request.form['password2']:
			new_user = User(
				email = request.form['email'], 
				password = generate_password_hash(request.form['password1'])
			)

			db.session.add(new_user)
			db.session.commit()

			return redirect(url_for('auth.login'))
		else:
			rta = "Password don't match"
			flash(rta, category='error')
			
			return render_template('signup.html', title=APP)


