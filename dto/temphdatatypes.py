import uuid


class TempHumidityMeasurements:
	"""
	This class represents a measurement from
	temperature humidity sensor
	default Node: 19, 22, 23, 24
	"""

	def __init__(self, ts, temp, temp_external, humidity, battery):
		"""
		:param ts: timestamp in the format of datetime.now()
		:param temp: float representing measurement of the temperature
		:param temp_external: float representing measurement of the external temperature
		:param humidity: float representing measurement of the humidity (relative)
		:param battery: float representing measurement of the battery
		:return:
		"""

		# the id of the record which will be stored in the database
		self.id = uuid.uuid4()

		# the UUID which represents the device itself
		self.deviceid = None  # todo macaddress or device id?
		self.type = 'temp_hum_measurement'

		self.ts = ts
		self.temp = temp
		self.temp_external = temp_external
		self.humidity = humidity
		self.battery = battery

	def standardize(self, name, rate):
		"""
		standardize the atr name by rate
		:param name:
		:param rate:
		:return:
		"""
		if name in self.__dict__:
			if name == 'temp':
				self.temp = self.temp * rate
			elif name == 'temp_external':
				self.temp_external = self.temp_external * rate
			elif name == 'humidity':
				self.humidity = self.humidity * rate
			elif name == 'battery':
				self.battery = self.battery * rate
		elif name == 'all':
			self.temp = self.temp * rate
			self.temp_external = self.temp_external * rate
			self.humidity = self.humidity * rate
			self.battery = self.battery * rate
		else:
			raise AttributeError(name)

	def __str__(self):
		return """#type:temp_hum_measurement#ts:%s#deviceid:%s#temprature:%s
		#external_temp:%s#humidity:%s#battery:%s""" % (self.ts, self.deviceid,
		                                               self.temp, self.temp_external,
		                                               self.humidity, self.battery)
