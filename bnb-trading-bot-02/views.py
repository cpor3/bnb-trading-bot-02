from flask import Blueprint, render_template, request, redirect, url_for, session, g
from flask_login import current_user, login_required
from .models import User, Bots
from . import db, APP
from .Bnb_Trading_Bot import Bot

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def index():

	return render_template('index.html', 
		title = APP,
		navbar = [
			{
				'text': 'Dashboard',
				'href': '/',
				'active': True
			},
			{
				'text': 'BOTs', 
				'href': '/bots',
				'active': False
			},
			{
				'text': 'Backtest',
				'href': '/backtest',
				'active': False
			}
		]
	)

@views.route('/simular', methods=['POST'])
@login_required
def simular():
	from . import client, app

	PAR1 = request.form['PAR1']
	PAR2 = request.form['PAR2']
	saldo_inicial = request.form['saldo']
	Date_desde = request.form['F_Desde_date'] + " " + request.form['F_Desde_time'] + " UTC"
	Date_hasta = request.form['F_Hasta_date'] + " " + request.form['F_Hasta_time'] + " UTC"

	bot = Bot(client)
	bot.set_crypto(PAR1, PAR2)
	bot.simulate(Date_desde, Date_hasta, saldo_inicial)

	g.bots[current_user.get_id()] = bot

	return render_template('ejecutando_backtest.html', 
		title=APP,
		navbar = [
			{
				'text': 'Dashboard',
				'href': '/',
				'active': False
			},
			{
				'text': 'BOTs', 
				'href': '/bots',
				'active': False
			},
			{
				'text': 'Backtest',
				'href': '#',
				'active': True
			}
		]
	)

@views.route('/backtest_status')
@login_required
def backtest_status():
	print()
	rendered_status = g.bots[current_user.get_id()].rendered_status

	return rendered_status

@views.route('/backtest_result')
@login_required
def backtest_result():
	rendered_data = g.bots[current_user.get_id()].rendered_data
	g.bots.pop(current_user.get_id())

	return render_template('simular.html', 
		title = APP,
		navbar = [
			{
				'text': 'Dashboard',
				'href': '/',
				'active': False
			},
			{
				'text': 'BOTs', 
				'href': '/bots',
				'active': False
			},
			{
				'text': 'Backtest',
				'href': '#',
				'active': True
			}
		],
		klines = rendered_data['klines'], 
		MA = rendered_data['MA'],
		trades = rendered_data['trades'], 
		transactions = rendered_data['transactions'],
		starting_capital = rendered_data['starting_capital'],
		current_wallet = rendered_data['current_wallet'],		
		strategy_result = rendered_data['strategy_result'], 
		strategy_result_pct = rendered_data['strategy_result_pct'], 
		par = rendered_data['par'],
		par1 = rendered_data['par1'],
		par2 = rendered_data['par2'],
		desde = rendered_data['desde'],
		hasta = rendered_data['hasta'],
		intervalo = rendered_data['intervalo'],
		media = rendered_data['media'],
		tendencia = rendered_data['tendencia'],
		price_precision = rendered_data['price_precision'],
		quantity_precision = rendered_data['quantity_precision']
	)

@views.route('/bots')
@login_required
def bots():

	user_bots = Bots.query.filter_by(user_id = current_user.id)

	return render_template('bots.html', 
		title=APP,
		navbar = [
			{
				'text': 'Dashboard',
				'href': '/',
				'active': False
			},
			{
				'text': 'BOTs', 
				'href': '#',
				'active': True
			},
			{
				'text': 'Backtest',
				'href': '/backtest',
				'active': False
			}
		],
		user_bots = user_bots
	)

@views.route('/new_bot', methods=['GET', 'POST'])
@login_required
def new_bot():
	if request.method == 'GET':
		pares1 = []
		pares2 = []

		from . import exchangeInfo
		symbols = exchangeInfo['symbols']

		for symbol in symbols:
			pares1.append(symbol['baseAsset'])

		for symbol in symbols:
			pares2.append(symbol['quoteAsset'])

		return render_template('new_bot.html', 
			pares1=list(dict.fromkeys(pares1)), 
			pares2=list(dict.fromkeys(pares2)),
			navbar = [
				{
					'text': 'Dashboard',
					'href': '/',
					'active': False
				},
				{
					'text': 'BOTs', 
					'href': '#',
					'active': True
				},
				{
					'text': 'Backtest',
					'href': '/backtest',
					'active': False
				}
			]
		)
	else:
		new_bot_obj = Bots(
			name = request.form['name'],
			par1 = request.form['PAR1'],
			par2 = request.form['PAR2'],
			par = request.form['PAR1'] + request.form['PAR2'],
			status = "stopped",
			user_id = current_user.id,
			starting_capital = 0.0,
			current_wallet = 0.0
		)
		db.session.add(new_bot_obj)
		db.session.commit()

		return redirect(url_for('views.bots'))

@views.route('/backtest')
@login_required
def backtest():
	pares1 = []
	pares2 = []

	from . import exchangeInfo
	symbols = exchangeInfo['symbols']

	for symbol in symbols:
		pares1.append(symbol['baseAsset'])

	for symbol in symbols:
		pares2.append(symbol['quoteAsset'])

	return render_template('backtest.html', 
		title=APP,
		pares1=list(dict.fromkeys(pares1)), 
		pares2=list(dict.fromkeys(pares2)),
		navbar = [
			{
				'text': 'Dashboard',
				'href': '/',
				'active': False
			},
			{
				'text': 'BOTs', 
				'href': '/bots',
				'active': False
			},
			{
				'text': 'Backtest',
				'href': '#',
				'active': True
			}
		]
	)

@views.route('/mem')
def show_mem():
	msj = f"len(g.bots) = {len(g.bots)}"

	return msj

###### Infinite Thread #######

@views.route('/init_thread')
def init_infinite_thread():

	if not g.infinite_thread.is_active():
		g.infinite_thread.start()

		print('Infinite thread created at: {}'.format(g.infinite_thread.start_time))

		return 'Infinite thread started at: ' + g.infinite_thread.start_time
	else:
		return 'Infinite thread already active'

@views.route('/stop_thread')
def stop_thread():
	g.infinite_thread.stop()

	return 'Stopping infinite thread...'

@views.route('/thread_status')
def thread_status():
	if g.infinite_thread.is_active():
		return "Thread initiated at " + g.infinite_thread.start_time + ". Current value: " + str(g.infinite_thread.counter)
	else:
		return "Thread not initiated. Current value: " + str(g.infinite_thread.counter)
