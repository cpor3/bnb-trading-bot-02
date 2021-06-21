from flask import Blueprint, render_template, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		name = request.form['user']
		password = request.form['password']

		user_logged = User.query.filter_by(name=name).first()

		if user_logged:
			if user_logged.password == password:
				login_user(user_logged)
				rta = f"Usuario {user_logged.name} logeado"
				session['temp_var'] = rta
			else:
				rta = "Password incorrecta"
		else:
			rta = "Usuario no existe"

		print(rta)

	return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
	session.pop('temp_var')
	logout_user()

	return render_template('index.html')