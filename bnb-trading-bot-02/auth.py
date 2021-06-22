from flask import Blueprint, render_template, request, session, redirect, url_for
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
				return redirect(url_for('views.index'))
			else:
				rta = "Password incorrecta"
		else:
			rta = "Usuario no existe"

		print(rta)

	return render_template('login.html', title=__name__)

@auth.route('/logout')
@login_required
def logout():
	logout_user()

	return redirect(url_for('views.index'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'GET':
		return render_template('signup.html', title=__name__)
	else:
		name = request.form['email']
		password = request.form['password1']

		new_user = User(name=name, password=password)
		db.session.add(new_user)
		db.session.commit()

		return redirect(url_for('auth.login'))

