from binance.client import Client #verr
from binance.helpers import *
import threading
import copy

from . import config_api
from . import to_LightWeightChartFormat
from .Client_Learn import Client_Learn
from .Trading_Analysis import interval_to_mins, tendencia, tendencia_offline, MA, create_offline_MA

INTERVALO = Client.KLINE_INTERVAL_5MINUTE # tiene que ser unos de los enums de python-binance
LONGITUD_MEDIA_MOVIL = 50
LONGITUD_TENDENCIA = 10

class Bot():
	def __init__(self, _client, _PAR1='', _PAR2='', _interval=INTERVALO, _long_tendencia=LONGITUD_TENDENCIA, _long_MA=LONGITUD_MEDIA_MOVIL):
		self.client = copy.deepcopy(_client)
		self.PAR1 = _PAR1
		self.PAR2 = _PAR2
		self.PAR = self.PAR1 + self.PAR2
		self.interval = _interval
		self.long_tendencia = _long_tendencia
		self.long_MA = _long_MA
		self.FACTOR_DE_COMPRA = 1 - 0.005 # 0,5% por debajo de la media
		self.SL = 1 - 0.01 # 1% por abajo del precio
		self.OCO_SL = 1 - 0.01 # 1% por abajo del precio
		self.OCO_TP = 1 + 0.02 # 2% por arriba del precio 
		self.reset()
		self.update_exchangeInfo()
	
	def set_crypto(self, _PAR1, _PAR2):
		self.PAR1 = _PAR1
		self.PAR2 = _PAR2
		self.PAR = self.PAR1 + self.PAR2

	def simulate(self, _Date_desde, _Date_hasta, _saldo_inicial):
		print('Creando thread de simulacion del bot')
		_thread = threading.Thread(target=self.backtest_thread, args=(_saldo_inicial, _Date_desde, _Date_hasta))
		_thread.start()
		print('Ejecutando thread de simulacion...')

	def update_exchangeInfo(self):
		self.exchangeInfo = self.client.get_exchange_info()

	def reset(self):
		self.trades = []
		self.transacciones = [0, 0]
		self.starting_capital = [[0.0, 0.0], [0.0, 0.0]]
		self.current_wallet = [[0.0, 0.0], [0.0, 0.0]]
		self.strategy_result = [0.0, 0.0]
		self.strategy_result_pct = [0.0, 0.0]
		self.rendered_data = {}
		self.rendered_status = {
			'percentaje': 0.0
		}

	def precision(self, number):

		number_string = str(number)
		integer_and_fraction = number_string.split('.')

		return len(integer_and_fraction[-1])

	def tickSize(self, par):

		for info in self.exchangeInfo['symbols']:
			if info['symbol'] == par:
				for _filter in info['filters']:
					if _filter['filterType'] == 'PRICE_FILTER':
						return float(_filter['tickSize'])

		return 0

	def stepSize(self, par):

		for info in self.exchangeInfo['symbols']:
			if info['symbol'] == par:
				for _filter in info['filters']:
					if _filter['filterType'] == 'LOT_SIZE':
						return float(_filter['stepSize'])

		return 0

	def precio(self, symbol):
		symbol_info = self.client.get_all_tickers(symbol)

		return float(symbol_info[0]['price'])

		#precios = client.get_all_tickers()
		#for precio in precios:
		#	if (precio['symbol'] == symbol):
		#		return float(precio['price'])
		#return 0

	def saldo(self, symbol):
		balance = self.client.get_asset_balance(asset=symbol)

		return float(balance['free'])

	def precio_ejecutado(self, orden):
		precio = 0.0

		for orden_parcial in orden['fills']:
			precio += float(orden_parcial['price'])

		return precio

	def comision_ejecutada(self, orden):
		comision = 0.0

		for orden_parcial in orden['fills']:
			comision += float(orden_parcial['commission'])

		return comision

	def ajustar_montos(self, orden=None):

		if orden != None:
			# ajustamos cantidades de transacciones
			self.transacciones[1] += 1
			
			# calculamos precio y comision de la orden ejecutada
			precio_ej = self.precio_ejecutado(orden)
			comision_ej = self.comision_ejecutada(orden)

			# actualizamos montos de la wallet, dependiendo si fue venta o compra
			if (orden['side'] == 'BUY'):
				self.current_wallet[0][1] += float(orden['executedQty'])
				self.current_wallet[1][1] = self.current_wallet[1][1] - precio_ej * float(orden['executedQty']) - comision_ej
			else:
				self.current_wallet[0][1] -= float(orden['executedQty'])
				self.current_wallet[1][1] = self.current_wallet[1][1] + precio_ej * float(orden['executedQty']) - comision_ej

			# solo en la primera transaccion replicamos los montos y cantidades en la estrategia Buy & Hold
			if (self.transacciones[1] == 1): 
				self.transacciones[0] = 1
				self.current_wallet[0][0] = self.current_wallet[0][1]
				self.current_wallet[1][0] = self.current_wallet[1][1]

		# ajustamos los resultados de las dos estrategias en funcion del valor actual del par
		# Buy & Hold
		self.strategy_result[0] = self.current_wallet[1][0] - self.starting_capital[1][0] + self.current_wallet[0][0] * self.precio(self.PAR)
		self.strategy_result_pct[0] = self.strategy_result[0] / self.starting_capital[1][0]

		# Bot
		self.strategy_result[1] = self.current_wallet[1][1] - self.starting_capital[1][1] + self.current_wallet[0][1] * self.precio(self.PAR)
		self.strategy_result_pct[1] = self.strategy_result[1] / self.starting_capital[1][1]

		return

	def backtest_thread(self, _saldo_inicial, Date_desde, Date_hasta):
		self.reset()

		saldo_inicial = _saldo_inicial
		Date_desde = Date_desde
		Date_hasta = Date_hasta

		SIMULACION_INICIO = date_to_milliseconds(Date_desde) + 3 * 60 * 60 * 1000 
		SIMULACION_FIN = date_to_milliseconds(Date_hasta) + 3 * 60 * 60 * 1000

		delta_ms = (self.long_tendencia + self.long_MA) * interval_to_mins(self.interval) * 60 * 1000
		FECHA_HORA_INICIO_DATA = SIMULACION_INICIO - delta_ms

		print('Inicializando valores en modo TEST...')
		self.client.set_crypto(self.PAR1, self.PAR2)
		self.client.set_simulation_times_ms(SIMULACION_INICIO, SIMULACION_FIN)
		self.client.set_asset_balance(self.PAR1, "0.0")
		self.client.set_asset_balance(self.PAR2, saldo_inicial)
		self.client.get_offline_historical_klines(
			symbol = self.PAR, 
			interval_enum = self.interval, 
			start_str = FECHA_HORA_INICIO_DATA, 
			end_str = SIMULACION_FIN
		)
		MA_offline = create_offline_MA(
			self.client,
			self.long_tendencia, 
			self.long_MA, 
			self.PAR, 
			FECHA_HORA_INICIO_DATA, 
			SIMULACION_FIN, 
			self.interval
		)
		print('Modo TEST listo.\nArrancando simulacion...')
	#	time.sleep(2)

		self.starting_capital[0][0] = self.saldo(self.PAR1)
		self.starting_capital[0][1] = self.starting_capital[0][0]
		self.starting_capital[1][0] = self.saldo(self.PAR2)
		self.starting_capital[1][1] = self.starting_capital[1][0]

		self.current_wallet[0][0] = self.saldo(self.PAR1)
		self.current_wallet[0][1] = self.starting_capital[0][0]
		self.current_wallet[1][0] = self.saldo(self.PAR2)
		self.current_wallet[1][1] = self.starting_capital[1][0]

		_stepSize = self.stepSize(self.PAR) #cantidad
		stepSize_precision = self.precision(_stepSize)
		_tickSize = self.tickSize(self.PAR) #precio
		tickSize_precision = self.precision(_tickSize)

		on_time = True
		while on_time:
			if 1:
	#		try:
				on_time = self.client.update_time()

	#			pendiente_de_la_media = tendencia(self.long_tendencia, self.long_MA, self.interval)
				pendiente_de_la_media = tendencia_offline(self.long_tendencia, self.long_MA, self.interval, self.client.current_time_ms, MA_offline, SIMULACION_INICIO)

				if (pendiente_de_la_media > 0): # tendencia de la media movil positiva

					precio_actual = self.precio(self.PAR)

	#				precio_compra = MA(self.client, self.long_MA, PAR, "now UTC", self.interval) * FACTOR_DE_COMPRA # x% por debajo de la media
					MA_index = int(((self.client.current_time_ms - SIMULACION_INICIO) / interval_to_milliseconds(self.interval)) + self.long_tendencia)
					precio_compra = MA_offline[MA_index] * self.FACTOR_DE_COMPRA # x% por debajo de la media
					
					if (precio_actual < precio_compra): # precio competitivo

						qty = round(self.current_wallet[1][1] / (precio_actual * (1 + config_api.COMISION_BINANCE)), stepSize_precision) - _stepSize

						# compramos a precio de mercado
						orden_compra = self.client.order_market_buy(
							symbol = self.PAR, 
							quantity = qty
						)
	#					time.sleep(3)

						# ajustamos los montos y transacciones
						self.ajustar_montos(orden_compra)

	#					mostrar_dashboard()
						print('Comprados', float(orden_compra['executedQty']), self.PAR, 'a', self.precio_ejecutado(orden_compra), '!\n')

						self.trades.append({
							'Id': self.transacciones[1],
							'time': self.client.current_time_ms/1000.0, 
							'price': self.precio_ejecutado(orden_compra),
							'side': 'BUY',
							'qty': float(orden_compra['executedQty']),
							'strategy_result': self.strategy_result[1],
							'strategy_result_pct': self.strategy_result_pct[1]
						})

						# colocamos la orden de venta SL
						qty = self.current_wallet[0][1]
						SL_price = precio_actual * self.SL
						SL_stopPrice = SL_price

						print('Colocando orden de venta SL:', qty, self.PAR, 'a', SL_price, ', Stop Loss en', SL_stopPrice)
						orden_venta = self.client.order_limit_sell(
							symbol = self.PAR, 
							quantity = qty, 
							price = SL_price,
							stopPrice = SL_stopPrice,
							timeInForce = 'GTC'
						)
						#time.sleep(3)
						print('Orden de venta SL colocada! Esperando la venta....')

						# ejecutamos TRAILING STOP
						while (orden_venta['status'] != 'FILLED') and on_time:
							on_time = self.client.update_time(interval_to_mins(self.interval) * 60 * 1000)

							#simulamos la SL para ver si se vendio
							self.client.order_limit_sell_simulacion(
								orden_venta = orden_venta, 
								SL_stopPrice = SL_stopPrice 
							)
							#time.sleep(10)

							if (orden_venta['status'] == 'FILLED'):
								continue

							#revisamos el precio actual y el SL que le corresponderia
							nuevo_precio = self.precio(self.PAR)
							nuevo_SL = nuevo_precio * self.SL

							#si subio el precio actualizamos el SL
							if nuevo_SL > SL_stopPrice:
								#actualizamos el valor del SL
								SL_price = nuevo_SL
								SL_stopPrice = nuevo_SL

								#cancelamos la SL vigente
								print('Cancelando SL...\n')
								self.client.cancel_order(
									symbol = self.PAR,
									orderId = orden_venta['orderId']
								)

								#creamos la nueva
								print('Colocando orden de venta SL:', qty, self.PAR, 'a', SL_price, ', Stop Loss en', SL_stopPrice)
								orden_venta = self.client.order_limit_sell(
									symbol = self.PAR, 
									quantity = qty, 
									price = SL_price,
									stopPrice = SL_stopPrice,
									timeInForce = 'GTC'
								)
								print('Orden de venta SL colocada! Esperando la venta....')

								#on_time = self.client.update_time(interval_to_mins(self.interval) * 60 * 1000)

						# si la orden sigue sin ejecutarse salimos del while anterior por on_time=false -> terminamos
						if orden_venta['status'] != 'FILLED':
							break

						self.ajustar_montos(orden_venta)

						print('Vendidos', float(orden_venta['executedQty']), self.PAR, 'a', self.precio_ejecutado(orden_venta), '!')
						print(' ')

						self.trades.append({
							'Id': self.transacciones[1],
							'time': self.client.current_time_ms/1000.0, 
							'price': self.precio_ejecutado(orden_venta),
							'side': 'SELL',
							'qty': float(orden_venta['executedQty']),
							'strategy_result': self.strategy_result[1],
							'strategy_result_pct': self.strategy_result_pct[1]
						})

						print('Esperando nuevo momento para comprar...')

						# si la SL se completo con perdida, no volvemos a comprar por las proximas 5 velas
						if self.precio_ejecutado(orden_venta) < precio_actual:
							on_time = self.client.update_time(5 * interval_to_mins(self.interval) * 60 * 1000) # 10 velas

						# avanzamos a la proxima vela (=intervalo), multiplicamos * 60 * 1000 para llevar a milisegundos 
						on_time = self.client.update_time(interval_to_mins(self.interval) * 60 * 1000)

						# actualizamos el porcentaje completado de la simulacion 
						self.rendered_status['percentaje'] = (self.client.current_time_ms - SIMULACION_INICIO) / (SIMULACION_FIN - SIMULACION_INICIO)

		#actualizamos resultados en funcion del precio actual del par
		self.ajustar_montos()
		klines_converted, MA_offline_converted = to_LightWeightChartFormat(self.client.offline_klines, MA_offline)

		self.rendered_data = {
			'klines': klines_converted, 
			'MA': MA_offline_converted,
			'trades': self.trades, 
			'transactions': self.transacciones,
			'starting_capital': self.starting_capital,
			'current_wallet': self.current_wallet,		
			'strategy_result': self.strategy_result, 
			'strategy_result_pct': self.strategy_result_pct, 
			'par': self.PAR,
			'par1': self.PAR1,
			'par2': self.PAR2,
			'desde': SIMULACION_INICIO / 1000,
			'hasta': SIMULACION_FIN / 1000,
			'intervalo': interval_to_mins(self.interval),
			'media': self.long_MA,
			'tendencia': self.long_tendencia,
			'price_precision': tickSize_precision,
			'quantity_precision': stepSize_precision
		}

		self.rendered_status['percentaje'] = 1.0

		return

