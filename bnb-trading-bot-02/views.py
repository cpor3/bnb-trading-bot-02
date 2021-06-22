from flask import Blueprint, render_template, request, session, g
from flask_login import current_user
from .models import User
from . import db
from .Bnb_Trading_Bot import Bot

views = Blueprint('views', __name__)

@views.route('/simular', methods=['POST'])
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

	return render_template('ejecutando_backtest.html')

@views.route('/backtest_status')
def backtest_status():
	print()
	rendered_status = g.bots[current_user.get_id()].rendered_status

	return rendered_status

@views.route('/backtest_result')
def backtest_result():
	rendered_data = g.bots[current_user.get_id()].rendered_data
	g.bots.pop(current_user.get_id())

	return render_template('simular.html', 
		title = rendered_data['title'],
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
def bots():

	return render_template('bots.html', 
		title=__name__
	)

@views.route('/backtest')
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
		title=__name__,
		pares1=list(dict.fromkeys(pares1)), 
		pares2=list(dict.fromkeys(pares2))
	)

@views.route('/')
def index():

	return render_template('index.html', 
		title=__name__,
		user=current_user
	)

@views.route('/w')
def w():
	session['temp_var'] = "temp_var creada"

	return session['temp_var']

@views.route('/r')
def r():
	if 'temp_var' in session:
		return session['temp_var']
	else:
		return 'No temp_var in session'

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

@views.route('/write', methods=['GET', 'POST'])
def write():
	new_user = User(name="cpor33", password="1234566")
	db.session.add(new_user)
	db.session.commit()

	return "registro agregado"

@views.route('/read')
def read():
	libro = Libro.query.get(2)
	print(libro.id)
	print(libro.nombre)
	print(libro.cantidad)

	return "registro leido"
