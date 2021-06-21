from binance.helpers import *
import numpy as np

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
	from . import client
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
	from . import client
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
