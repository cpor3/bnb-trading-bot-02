from flask import *
from binance.client import Client
from binance.enums import *
from binance.helpers import *
from . import config_api
from .Client_Learn import Client_Learn
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time
import threading
import requests
import signal 
import os

INTERVALO = Client.KLINE_INTERVAL_5MINUTE # tiene que ser unos de los enums de python-binance
LONGITUD_MEDIA_MOVIL = 50
LONGITUD_TENDENCIA = 10
FACTOR_DE_COMPRA = 1 - 0.005 # 0,5% por debajo de la media
OCO_SL = 1 - 0.01 # 1% por abajo del precio
OCO_TP = 1 + 0.02 # 2% por arriba del precio 

SIMULACION_INICIO = "2021-03-31 00:00:00 UTC" # ARGENTINA es 3hs menos que UTC
SIMULACION_FIN = "2021-03-31 22:00:00 UTC" # ARGENTINA es 3hs menos que UTC

def iniciar_API():
	global client

	print('Inicializando API...')
	client = Client(config_api.API_Key, config_api.Secret_Key)
	time.sleep(1)
	print('API lista.\n')

	return

def iniciar_API_test():
	global client

	print('\nInicializando API...')
#	client = Client_Learn(config_api.API_Key, config_api.Secret_Key, SIMULACION_INICIO, SIMULACION_FIN)
	client = Client_Learn(config_api.API_Key, config_api.Secret_Key)
#	time.sleep(1)
	print('API lista.\n')

	return None

def interval_to_mins(interval):
	if (interval == '1m'):
		return 1
	elif (interval == '3m'):
		return 3 	
	elif (interval == '5m'):
		return 5 	
	elif (interval == '15m'):
		return 15 	
	elif (interval == '30m'):
		return 30 	
	elif (interval == '1h'):
		return 1 * 60 	
	elif (interval == '2h'):
		return 2 * 60 	
	elif (interval == '4h'):
		return 4 * 60  	
	elif (interval == '6h'):
		return 6 * 60  	
	elif (interval == '8h'):
		return 8 * 60  	
	elif (interval == '12h'):
		return 12 * 60  	
	elif (interval == '1d'):
		return 24 * 60  	
	elif (interval == '3d'):
		return 3 * 24 * 60  	
	elif (interval == '1w'):
		return 7 * 24 * 60  	
	elif (interval == '1M'):
		return 30 * 7 * 24 * 60  	

	return 0

def create_offline_MA(qty_muestras, length:int, symbol, start_str, end_str, interval_enum):
	MA = []

	if type(end_str) == int:
		end_ms = end_str
	else:
		end_ms = date_to_milliseconds(end_str)

	if type(start_str) == int:
		start_ms = start_str
	else:
		start_ms = date_to_milliseconds(start_str)

	interval_mins = interval_to_mins(interval_enum)

	delta_ms = int(length * interval_mins * 60 * 1000) # tamaño MA * x minutos * 60 segundos * 1000 milisegundos
	range_ms = start_ms - (qty_muestras * interval_mins * 60 * 1000) - delta_ms 
	
	klines = client.get_historical_klines(symbol = symbol, interval = interval_enum, start_str = range_ms, end_str = end_ms, limit=1000)
	klines_np = np.array(klines)
	klines_np = klines_np.astype(np.float)

	for i in range(len(klines) - length + 1):		
		MA.append( np.sum(klines_np[i:i+length, 4]) / length )

	return MA

def MA(length, symbol, end_str, interval_enum):
	qty = 0
	sum = 0.0

	if type(end_str) == int:
		end_ms = end_str
	else:
		end_ms = date_to_milliseconds(end_str)

	interval_mins = interval_to_mins(interval_enum)
	delta_ms = int(length * interval_mins * 60 * 1000) # tamaño MA * x minutos * 60 segundos * 1000 milisegundos
	start_ms = end_ms - delta_ms 
	
	klines = client.get_historical_klines(symbol = symbol, interval = interval_enum, start_str = start_ms, end_str = end_ms, limit=1000)

	for kline in reversed(klines):
		qty = qty + 1
		if (qty <= length):	# tomamos solo los ultimos length valores (por si el rango que tomamos fue mayor)
				sum = sum + float(kline[4]) # kline[4] es el precio de cierre

#	print('MA', '{:10.8f}'.format(sum/length), 'Qty:', qty)
	return (sum / length)

def tendencia(qty_muestras, length, interval_enum, current_time_ms):
	x = []
	y = []

	interval_mins = interval_to_mins(interval_enum)

	for i in range(qty_muestras):
		end_date_ms = current_time_ms - i * interval_mins * 60 * 1000
#		end_date = str(i * interval_mins) + " minutes ago UTC"
		media = MA(length, PAR, end_date_ms, interval_enum)
#		media = MA(length, PAR, end_date, interval_enum)
		x.append(i)
		y.append(media)

	params_polinomio = np.polyfit(x, y, 1) # aproximamos con una recta la evolucion de la media

#	print('{:3.2f}'.format(params_polinomio[0] * -1))
	return params_polinomio[0] * -1 # el indice 0 es la pendiente de la recta. multiplicamos por -1 porque la recta esta invertida

def tendencia_offline(qty_muestras, length, interval_enum, current_time_ms, MA_offline, init_time_ms):
	x = []
	y = []

	interval_ms = interval_to_milliseconds(interval_enum)

	for i in range(qty_muestras):
		MA_index = int(((current_time_ms - (i * interval_ms) - init_time_ms) / interval_ms) + qty_muestras)
		x.append(i)
		y.append(MA_offline[MA_index])

	params_polinomio = np.polyfit(x, y, 1)

	return params_polinomio[0] * -1 

def precio(symbol):

	symbol_info = client.get_all_tickers(symbol)

	return float(symbol_info[0]['price'])
"""
	precios = client.get_all_tickers()
	
	for precio in precios:
		if (precio['symbol'] == symbol):
			return float(precio['price'])
	return 0
"""

def saldo(symbol):

	balance = client.get_asset_balance(asset=symbol)

	return float(balance['free'])

def precio_ejecutado(orden):
	precio = 0.0

	for orden_parcial in orden['fills']:
		precio += float(orden_parcial['price'])

	return precio

def comision_ejecutada(orden):
	comision = 0.0

	for orden_parcial in orden['fills']:
		comision += float(orden_parcial['commission'])

	return comision

def ajustar_montos(orden=None):
	global transacciones
	global starting_capital
	global current_wallet
	global strategy_result
	global strategy_result_pct

	if orden != None:
		# ajustamos cantidades de transacciones
		transacciones[1] += 1
		
		# calculamos precio y comision de la orden ejecutada
		precio_ej = precio_ejecutado(orden)
		comision_ej = comision_ejecutada(orden)

		# actualizamos montos de la wallet, dependiendo si fue venta o compra
		if (orden['side'] == 'BUY'):
			current_wallet[0][1] += float(orden['executedQty'])
			current_wallet[1][1] = current_wallet[1][1] - precio_ej * float(orden['executedQty']) - comision_ej
		else:
			current_wallet[0][1] -= float(orden['executedQty'])
			current_wallet[1][1] = current_wallet[1][1] + precio_ej * float(orden['executedQty']) - comision_ej

		# solo en la primera transaccion replicamos los montos y cantidades en la estrategia Buy & Hold
		if (transacciones[1] == 1): 
			transacciones[0] = 1
			current_wallet[0][0] = current_wallet[0][1]
			current_wallet[1][0] = current_wallet[1][1]

	# ajustamos los resultados de las dos estrategias en funcion del valor actual del par
	# Buy & Hold
	strategy_result[0] = current_wallet[1][0] - starting_capital[1][0] + current_wallet[0][0] * precio(PAR)  #- starting_capital[0][0] * precio(PAR)
	strategy_result_pct[0] = strategy_result[0] / starting_capital[1][0]

	# Bot
	strategy_result[1] = current_wallet[1][1] - starting_capital[1][1] + current_wallet[0][1] * precio(PAR)  #- starting_capital[0][1] * precio(PAR)
	strategy_result_pct[1] = strategy_result[1] / starting_capital[1][1]

	return

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

def precision(number):

	number_string = str(number)
	integer_and_fraction = number_string.split('.')

	return len(integer_and_fraction[-1])

def tickSize(par):

	for info in exchangeInfo['symbols']:
		if info['symbol'] == par:
			for _filter in info['filters']:
				if _filter['filterType'] == 'PRICE_FILTER':
					return float(_filter['tickSize'])

	return 0

def stepSize(par):

	for info in exchangeInfo['symbols']:
		if info['symbol'] == par:
			for _filter in info['filters']:
				if _filter['filterType'] == 'LOT_SIZE':
					return float(_filter['stepSize'])

	return 0

app = Flask(__name__)

@app.route('/simular', methods=['POST'])
def simular():
	PAR1 = request.form['PAR1']
	PAR2 = request.form['PAR2']
	saldo_inicial = request.form['saldo']
	Date_desde = request.form['F_Desde_date'] + " " + request.form['F_Desde_time'] + " UTC"
	Date_hasta = request.form['F_Hasta_date'] + " " + request.form['F_Hasta_time'] + " UTC"

	print('Creando la thread de simulacion')
	backtest_thread = threading.Thread(target=simular_thread, args=(PAR1, PAR2, saldo_inicial, Date_desde, Date_hasta))
	print('Ejecutando thread de simulacion...')
	backtest_thread.start()

	return render_template('ejecutando_backtest.html')

@app.route('/backtest_status')
def backtest_status():
	return rendered_status

@app.route('/backtest_result')
def backtest_result():
	global rendered_status
	global rendered_data

	rendered_status['percentaje'] = 0.0

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

def simular_thread(_PAR1, _PAR2, _saldo_inicial, Date_desde, Date_hasta):
	global PAR
	global PAR1
	global PAR2
	global trades
	global transacciones
	global starting_capital
	global current_wallet
	global strategy_result
	global strategy_result_pct
	global rendered_status
	global rendered_data

	transacciones = [0, 0]
	starting_capital = [[0.0, 0.0], [0.0, 0.0]]
	current_wallet = [[0.0, 0.0], [0.0, 0.0]]
	strategy_result = [0.0, 0.0]
	strategy_result_pct = [0.0, 0.0]

	PAR1 = _PAR1
	PAR2 = _PAR2
	PAR = PAR1 + PAR2
	saldo_inicial = _saldo_inicial
	Date_desde = Date_desde
	Date_hasta = Date_hasta
	SIMULACION_INICIO = date_to_milliseconds(Date_desde) + 3 * 60 * 60 * 1000
	SIMULACION_FIN = date_to_milliseconds(Date_hasta) + 3 * 60 * 60 * 1000

	trades = []

	delta_ms = (LONGITUD_TENDENCIA + LONGITUD_MEDIA_MOVIL) * interval_to_mins(INTERVALO) * 60 * 1000
	FECHA_HORA_INICIO_DATA = SIMULACION_INICIO - delta_ms

	print('Inicializando valores en modo TEST...')
	client.set_crypto(PAR1, PAR2)
	client.set_simulation_times_ms(SIMULACION_INICIO, SIMULACION_FIN)
	client.set_asset_balance(PAR1, "0.0")
	client.set_asset_balance(PAR2, saldo_inicial)
	client.get_offline_historical_klines(
		symbol = PAR, 
		interval_enum = INTERVALO, 
		start_str = FECHA_HORA_INICIO_DATA, 
		end_str = SIMULACION_FIN
	)
	MA_offline = create_offline_MA(LONGITUD_TENDENCIA, 
		LONGITUD_MEDIA_MOVIL, 
		PAR, 
		FECHA_HORA_INICIO_DATA, 
		SIMULACION_FIN, 
		INTERVALO
	)

	print('Modo TEST listo.\nArrancando simulacion...')
#	time.sleep(2)

	starting_capital[0][0] = saldo(PAR1)
	starting_capital[0][1] = starting_capital[0][0]
	starting_capital[1][0] = saldo(PAR2)
	starting_capital[1][1] = starting_capital[1][0]

	current_wallet[0][0] = saldo(PAR1)
	current_wallet[0][1] = starting_capital[0][0]
	current_wallet[1][0] = saldo(PAR2)
	current_wallet[1][1] = starting_capital[1][0]

	_stepSize = stepSize(PAR) #cantidad
	stepSize_precision = precision(_stepSize)
	_tickSize = tickSize(PAR) #precio
	tickSize_precision = precision(_tickSize)

	on_time = True
	while on_time:
		if 1:
#		try:
			on_time = client.update_time()

#			pendiente_de_la_media = tendencia(LONGITUD_TENDENCIA, LONGITUD_MEDIA_MOVIL, INTERVALO)
			pendiente_de_la_media = tendencia_offline(LONGITUD_TENDENCIA, LONGITUD_MEDIA_MOVIL, INTERVALO, client.current_time_ms, MA_offline, SIMULACION_INICIO)

			if (pendiente_de_la_media > 0): # tendencia de la media movil positiva

				precio_actual = precio(PAR)

#				precio_compra = MA(LONGITUD_MEDIA_MOVIL, PAR, "now UTC", INTERVALO) * FACTOR_DE_COMPRA # x% por debajo de la media
				MA_index = int(((client.current_time_ms - SIMULACION_INICIO) / interval_to_milliseconds(INTERVALO)) + LONGITUD_TENDENCIA)
				precio_compra = MA_offline[MA_index] * FACTOR_DE_COMPRA # x% por debajo de la media
				
				if (precio_actual < precio_compra): # precio competitivo

					qty = round(current_wallet[1][1] / (precio_actual * (1 + config_api.COMISION_BINANCE)), stepSize_precision) - _stepSize

					# compramos a precio de mercado
					orden_compra = client.order_market_buy(
						symbol=PAR, 
						quantity=qty
					)
#					time.sleep(3)

					# ajustamos los montos y transacciones
					ajustar_montos(orden_compra)

#					mostrar_dashboard()
					print('Comprados', float(orden_compra['executedQty']), PAR, 'a', precio_ejecutado(orden_compra), '!\n')
					print('MA:', MA_offline[MA_index])
					print('')

					trades.append({
						'Id': transacciones[1],
						'time': client.current_time_ms/1000.0, 
						'price': precio_ejecutado(orden_compra),
						'side': 'BUY',
						'qty': float(orden_compra['executedQty']),
						'strategy_result': strategy_result[1],
						'strategy_result_pct': strategy_result_pct[1]
					})

					# colocamos la orden de venta OCO
					qty = current_wallet[0][1]
					oco_price = precio_actual * OCO_TP
					oco_stopPrice = precio_actual * OCO_SL
					oco_stopLimitPrice = oco_stopPrice

					print('Colocando orden de venta OCO:', qty, PAR, 'a', oco_price, ', Stop Loss en', oco_stopPrice)

					orden_venta = client.order_oco_sell(
						symbol = PAR, 
						quantity = qty, 
						price = oco_price,
						stopPrice = oco_stopPrice,
						stopLimitPrice = oco_stopPrice,
						stopLimitTimeInForce = 'GTC'
					)
#					time.sleep(3)

					print('Orden de venta OCO colocada! Esperando la venta....')
					
					# esperamos hasta que se ejecute la OCO
					while (orden_venta['status'] != 'FILLED') and on_time:
#						time.sleep(10)
						on_time = client.update_time(interval_to_mins(INTERVALO) * 60 * 1000)
						client.order_oco_sell_simulacion(
							orden_venta = orden_venta, 
							oco_price = oco_price, 
							oco_stopPrice = oco_stopPrice 
						)

					# si la orden sigue sin ejecutarse salimos del while anterior por on_time=false -> terminamos
					if orden_venta['status'] != 'FILLED':
						break

					ajustar_montos(orden_venta)

#					mostrar_dashboard()
					print('Vendidos', float(orden_venta['executedQty']), PAR, 'a', precio_ejecutado(orden_venta), '!')
					print(' ')

					trades.append({
						'Id': transacciones[1],
						'time': client.current_time_ms/1000.0, 
						'price': precio_ejecutado(orden_venta),
						'side': 'SELL',
						'qty': float(orden_venta['executedQty']),
						'strategy_result': strategy_result[1],
						'strategy_result_pct': strategy_result_pct[1]
					})

					print('Esperando nuevo momento para comprar...')

					# si la OCO se completo por el SL, no volvemos a comprar por las proximas 5 velas
					if precio_ejecutado(orden_venta) < precio_actual:
						on_time = client.update_time(5 * interval_to_mins(INTERVALO) * 60 * 1000) # 10 velas

					# avanzamos a la proxima vela (=intervalo), multiplicamos * 60 * 1000 para llevar a milisegundos 
					on_time = client.update_time(interval_to_mins(INTERVALO) * 60 * 1000)

					# actualizamos el porcentaje completado de la simulacion 
					rendered_status['percentaje'] = (client.current_time_ms - SIMULACION_INICIO) / (SIMULACION_FIN - SIMULACION_INICIO)

	#actualizamos resultados en funcion del precio actual del par
	ajustar_montos()
	klines_converted, MA_offline_converted = to_LightWeightChartFormat(client.offline_klines, MA_offline)

	rendered_data = {
		'title': __name__,
		'klines': klines_converted, 
		'MA': MA_offline_converted,
		'trades': trades, 
		'transactions': transacciones,
		'starting_capital': starting_capital,
		'current_wallet': current_wallet,		
		'strategy_result': strategy_result, 
		'strategy_result_pct': strategy_result_pct, 
		'par': PAR,
		'par1': PAR1,
		'par2': PAR2,
		'desde': SIMULACION_INICIO / 1000,
		'hasta': SIMULACION_FIN / 1000,
		'intervalo': interval_to_mins(INTERVALO),
		'media': LONGITUD_MEDIA_MOVIL,
		'tendencia': LONGITUD_TENDENCIA,
		'price_precision': tickSize_precision,
		'quantity_precision': stepSize_precision
	}

	rendered_status['percentaje'] = 1.0

	return

@app.route('/bots')
def bots():

	return render_template('bots.html', 
		title=__name__
	)

@app.route('/backtest')
def backtest():
	pares1 = []
	pares2 = []

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

@app.route('/')
def index():

	return render_template('index.html', 
		title=__name__
	)

@app.route('/init_thread')
def init_infinite_thread():
	global infinite_thread_init_time
	global infinite_thread_active
	global infinite_thread_var

	if not infinite_thread_active:
		print('Creating infinite thread')
		infinite_thread_active = True
		infinite_thread_var = 0
		infinite__thread = threading.Thread(target=infinite_thread)
		infinite__thread.setDaemon(True)
		infinite__thread.start()

		infinite_thread_init_time = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
		print('Infinite thread created at: {}'.format(infinite_thread_init_time))

		return 'Infinite thread started at: ' + infinite_thread_init_time
	else:
		return 'Infinite thread already active'

@app.route('/stop_thread')
def stop_thread():
	global infinite_thread_active

	infinite_thread_active = False
	return 'Stopping infinite thread...'

@app.route('/get_thread')
def get_thread():
	if infinite_thread_active:
		return "Thread initiated at " + infinite_thread_init_time + ". Current value: " + str(infinite_thread_var)
	else:
		return "Thread not initiated. Current value: " + str(infinite_thread_var)

def infinite_thread():
	global infinite_thread_var

	print('Running infinite thread...\n')

	while infinite_thread_active:
		infinite_thread_var += 1

		#enviamos un request cada 15 minutos
		if infinite_thread_var > 90:
			infinite_thread_var = 0
			requests.get('http://bnb-trading-bot-01.herokuapp.com')
			print('Request sent.')

		#cuando se recive una señal SIGTERM, tenemos 30 segundos para cerrar bien antes de recibir la SIGKILL 
		time.sleep(10) #el time.sleep tiene que ser corto

	print('Infinite thread stopped\n')
	return

@app.template_filter('datetime_format')
def dar_formato(time_unixstamp):

    return datetime.fromtimestamp(time_unixstamp)

@app.context_processor
def precision_filter():
	def _precision_filter(num, precision):
		return round(num, precision)

	return dict(precision_filter=_precision_filter)

def handle_SIGTERM(signalnum, stackframe):
	global infinite_thread_active

	print('SIGTERM signal received.')
	infinite_thread_active = False
	time.sleep(15) #esperamos al infinite thread para que se cierre 

	print('Exiting app')
	exit()


######################################

client = []
trades = []
PAR = ""
PAR1 = ""
PAR2 = ""
rendered_data = {}
rendered_status = {
	'percentaje': 0.0
}

#iniciar_API()
iniciar_API_test()

exchangeInfo = client.get_exchange_info()

transacciones = [0, 0]
starting_capital = [[0.0, 0.0], [0.0, 0.0]]
current_wallet = [[0.0, 0.0], [0.0, 0.0]]
strategy_result = [0.0, 0.0]
strategy_result_pct = [0.0, 0.0]

infinite_thread_var = 0
infinite_thread_active = False

ENV = os.environ.get('FLASK_ENV')
if ENV == 'development':
	print('WARNING: Development mode.\n')
else:
	signal.signal(signal.SIGTERM, handle_SIGTERM)
	init_infinite_thread()
