from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_login import LoginManager

from binance.client import Client
from binance.enums import *

from .Infinite_Thread import Infinite_Thread
from .Client_Learn import Client_Learn
from . import config_api

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time
import threading
import requests
import signal 
import os

APP = 'bnb-trading-bot-02'
APP_URI = f'https://{APP}.herokuapp.com'
DB_NAME = 'database.db'

SIMULACION_INICIO = "2021-03-31 00:00:00 UTC" # ARGENTINA es 3hs menos que UTC
SIMULACION_FIN = "2021-03-31 22:00:00 UTC" # ARGENTINA es 3hs menos que UTC

def iniciar_API(test=False):
	print('\nInicializando API...')
	if test:
		client = Client_Learn(config_api.API_Key, config_api.Secret_Key)
	else:
		client = Client(config_api.API_Key, config_api.Secret_Key)
	print('API lista.\n')

	return client

def to_LightWeightChartFormat(klines, MA):

	klines_converted_array = []
	MA_converted_array = []
	i = 0
	offset = len(klines) - len(MA)

	for kline in klines:
		data = dict()
		data['time'] = kline[0]/1000
		data['open'] = float(kline[1])
		data['high'] = float(kline[2])
		data['low'] = float(kline[3])
		data['close'] = float(kline[4])
		klines_converted_array.append(data)

		if i >= offset:
			data_MA = dict()
			data_MA['time'] = kline[0]/1000
			data_MA['value'] = MA[i - offset]
			MA_converted_array.append(data_MA)
		i += 1

	return klines_converted_array, MA_converted_array

def handle_SIGTERM(signalnum, stackframe):
	print('SIGTERM signal received.')

	infinite_thread.stop()
	time.sleep(15) #esperamos al infinite thread para que se cierre 

	print('Exiting app')
	exit()


######################################

db = SQLAlchemy()

def create_db(app):
	database_file = APP + '/' + DB_NAME

	if not os.path.exists(database_file):
		db.create_all(app=app)
		print(f'Se creo una nueva base de datos: {database_file}')
	else:
		print(f'Base de datos existente: {database_file}')

def create_app():
	app = Flask(__name__)

	app.config['SECRET_KEY'] = config_api.APP_SECRET_KEY
	app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

	db.init_app(app)

	from .views import views
	from .auth import auth
	app.register_blueprint(views, url_prefix='/')
	app.register_blueprint(auth, url_prefix='/')

	from .models import User
	create_db(app)

	login_manager = LoginManager()
	login_manager.login_view = 'auth.login'
	login_manager.init_app(app)

	@login_manager.user_loader
	def load_user(user_id):
	    return User.query.get(user_id)

	return app

app = create_app()

@app.template_filter('datetime_format')
def dar_formato(time_unixstamp):

	datetime_str = datetime.fromtimestamp(time_unixstamp, timezone.utc) - timedelta(hours=3)

	return datetime_str.strftime("%Y-%m-%d - %H:%M:%S")

@app.context_processor
def precision_filter():
	def _precision_filter(num, precision):
		return round(num, precision)

	return dict(precision_filter=_precision_filter)

client = iniciar_API(test=True)

from .Bnb_Trading_Bot import Bot
bots = dict()

@app.before_request
def before_request():
	g.bots = bots
	g.infinite_thread = infinite_thread

exchangeInfo = client.get_exchange_info()

print('Creating infinite thread')	
infinite_thread = Infinite_Thread(APP_URI + '/ping')

ENV = os.environ.get('FLASK_ENV')
if ENV == 'development':
	print('WARNING: Development mode.\n')
else:
	signal.signal(signal.SIGTERM, handle_SIGTERM)
	infinite_thread.start()
