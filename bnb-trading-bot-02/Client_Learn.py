from binance.client import Client
from binance.enums import *
from binance.helpers import *
from . import config_api
import time
import json

def get_kline_index_position(data, value):

	for i in range(len(data)):
		if (data[i][0] >= value):
			return i

	return len(data)-1

"""
Class definition
"""
class Client_Learn():

	def __init__(self, api_key, secret_key, init_time=None, end_time=None):
		
		self.offline_klines = []
		self.saldo = []
		self.par1 = ''
		self.par2 = ''
		self.crypto = ''
		self.orders = []
		self.orderId = 0

		if init_time != None:
			self.current_time_ms = date_to_milliseconds(init_time)
		if end_time != None:
			self.end_time_ms = date_to_milliseconds(end_time)		

		self.real_client = Client(api_key, secret_key)
		time.sleep(1)

	def set_simulation_times_ms(self, init_time, end_time):
		
		self.current_time_ms = init_time
		self.end_time_ms = end_time		

		return None

	def get_offline_historical_klines(self, symbol, interval_enum, start_str, end_str):

		print('Descargando la info de todos los klines...')
		self.offline_klines = self.real_client.get_historical_klines(symbol=symbol, interval = interval_enum, start_str = start_str, end_str = end_str, limit=1000)
		print('Info offline descargada.')

		return None

	def get_historical_klines(self, symbol, interval, start_str, end_str, limit=1000):

		if type(start_str) == int:
			start_ms = start_str
		else:
			start_ms = date_to_milliseconds(start_str)

		if type(end_str) == int:
			end_ms = end_str
		else:
			end_ms = date_to_milliseconds(end_str)

		start_index = get_kline_index_position(self.offline_klines, start_ms)
		end_index = get_kline_index_position(self.offline_klines, end_ms)

		return self.offline_klines[start_index:end_index+1][:]

	def set_asset_balance(self, asset, saldo):

		#si ya existe el par, actualizamos su saldo
		for symbol in self.saldo:
			if symbol['symbol'] == asset:
				symbol['free'] = saldo
				return

		#sino lo creamos y agregamos
		nuevo_saldo = dict()
		nuevo_saldo['symbol'] = asset
		nuevo_saldo['free'] = saldo

		self.saldo.append(nuevo_saldo)

		return None

	def get_asset_balance(self, asset):

		for saldo in self.saldo:
			if (saldo['symbol'] == asset):
				return saldo

		return False

	def get_all_tickers(self, symbol=None):

		ticker = dict()
		all_tickers = []

		index = get_kline_index_position(self.offline_klines, self.current_time_ms)

		ticker['symbol'] = self.crypto #no importa el argumento de llamada, devuelve la info del symbol self.crypto
		ticker['open'] = self.offline_klines[index][1] #no se usa
		ticker['high'] = self.offline_klines[index][2] #lo usamos para simular las ordenes OCO
		ticker['low'] = self.offline_klines[index][3] #lo usamos para simular las ordenes OCO
		ticker['price'] = self.offline_klines[index][4] #tomamos como precio actual al precio de cierre de la vela

		all_tickers.append(ticker)

		return all_tickers

	def get_exchange_info(self):

		return self.real_client.get_exchange_info()

	def ping(self):

		return self.real_client.ping()

	def set_crypto(self, par1, par2):

		self.par1 = par1
		self.par2 = par2
		self.crypto = par1 + par2

		return None

	def update_time(self, delta_ms=60000):

#		current_real_time_ms = date_to_milliseconds("now UTC")
#		delta_ms = current_real_time_ms - self.init_real_time_ms

#		self.current_time_ms = self.init_time_ms + delta_ms

		self.current_time_ms += delta_ms

		if (self.current_time_ms > self.end_time_ms):
			print('----- Simulacion recorrio todos los datos -----')
			return False

		return True

	def cancel_order(self, symbol, orderId):
		#no hace falta implementar nada por ahora

		return

	def order_market_buy(self, symbol, quantity):

		precios = self.get_all_tickers(symbol)
		precio_ej = float(precios[0]['price'])
		comision_ej = precio_ej * quantity * config_api.COMISION_BINANCE
		self.orderId += 1

		rta = {
		    "symbol": symbol,
		    "orderId": self.orderId,
		    "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
		    "transactTime": self.current_time_ms,
		    "price": "0.00000000",
		    "origQty": "0.00000000",
		    "executedQty": str(quantity),
		    "status": "FILLED",
		    "timeInForce": "GTC",
		    "type": "MARKET",
		    "side": "BUY",
		    "fills": [
		        {
		            "price": str(precio_ej),
		            "qty": str(quantity),
		            "commission": str(comision_ej),
		            "commissionAsset": self.par2
		        }
		    ]
		}

		self.orders.append(rta)

		return rta

	def order_limit_sell(self, symbol, quantity, price, timeInForce, stopPrice):

		self.orderId += 1

		rta = {
		    "symbol": symbol,
		    "orderId": self.orderId,
		    "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
		    "transactTime": 0,
		    "price": "0.00000000",
		    "origQty": "0.00000000",
		    "executedQty": str(quantity),
		    "status": "NEW",
		    "timeInForce": "GTC",
		    "type": "LIMIT",
		    "side": "SELL",
		    "fills": [
		        {
		            "price": "0.0",
		            "qty": str(quantity),
		            "commission": "0.0",
		            "commissionAsset": self.par2
		        }
		    ]
		}
		return rta

	def order_limit_sell_simulacion(self, orden_venta, SL_stopPrice):

		precios = self.get_all_tickers()
		precio_low = float(precios[0]['low'])

		if (precio_low < SL_stopPrice):
			precio_ej = SL_stopPrice
		else:
			return

		comision_ej = precio_ej * float(orden_venta['executedQty']) * config_api.COMISION_BINANCE
		
		orden_venta['status'] = 'FILLED'
		orden_venta['transactTime'] = self.current_time_ms
		orden_venta['fills'][0]['price'] = str(precio_ej)
		orden_venta['fills'][0]['commission'] = str(comision_ej)

		self.orders.append(orden_venta)

		return None

	def order_oco_sell(self, symbol, quantity, price, stopPrice, stopLimitPrice, stopLimitTimeInForce):

		rta = {
		    "symbol": symbol,
		    "orderId": 0,
		    "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
		    "transactTime": 0,
		    "price": "0.00000000",
		    "origQty": "0.00000000",
		    "executedQty": str(quantity),
		    "status": "NEW",
		    "timeInForce": "GTC",
		    "type": "OCO",
		    "side": "SELL",
		    "fills": [
		        {
		            "price": "0.0",
		            "qty": str(quantity),
		            "commission": "0.0",
		            "commissionAsset": self.par2
		        }
		    ]
		}
		return rta

	def order_oco_sell_simulacion(self, orden_venta, oco_price, oco_stopPrice):

		precios = self.get_all_tickers()
		precio_high = float(precios[0]['high'])
		precio_low = float(precios[0]['low'])

		if (precio_high > oco_price):
			precio_ej = oco_price
		elif (precio_low < oco_stopPrice):
			precio_ej = oco_stopPrice
		else:
			return

		comision_ej = precio_ej * float(orden_venta['executedQty']) * config_api.COMISION_BINANCE
		
		orden_venta['status'] = 'FILLED'
		orden_venta['transactTime'] = self.current_time_ms
		orden_venta['fills'][0]['price'] = str(precio_ej)
		orden_venta['fills'][0]['commission'] = str(comision_ej)

		self.orders.append(orden_venta)

		return None
