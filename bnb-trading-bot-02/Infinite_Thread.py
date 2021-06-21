import threading
import requests
import time
from datetime import datetime, timezone, timedelta

class Infinite_Thread():

	def __init__(self, app_ping_uri, update_interval_seg=90):
		self.__app_ping_uri = app_ping_uri
		self.counter = 0
		self.active = False
		self.update_interval_seg = update_interval_seg # 90 = 15 mintuos
		self.start_time = 0
		self.thread = threading.Thread(target=self.infinite_thread)
		self.thread.setDaemon(True)

	def start(self, start_counter=0):
		self.counter = start_counter
		self.active = True
		self.start_time = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
		self.thread.start()

	def stop(self):
		self.active = False

	def is_active():
		return self.active

	def infinite_thread(self):
		print('Running infinite thread...\n')

		while self.active:
			self.counter += 1

			#enviamos un request cada 15 minutos
			if self.counter > self.update_interval_seg:
				self.counter = 0
				requests.get(self.__app_ping_uri)
				print('Request sent.')

			#en Heroku, cuando se recive una señal SIGTERM, tenemos 30 segundos para cerrar bien antes de recibir la SIGKILL 
			time.sleep(10) #el time.sleep tiene que ser corto

		print('Infinite thread stopped\n')

