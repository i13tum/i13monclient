import uuid


class PowerMeasurement:
    """
    This class represents a measurement from RFMPi
    default Node: 10
    """
    def __init__(self, ts, p1=None, p2=None, p3=None, p4=None, vrms=None, temperature=None):
        """
        :param ts: timestamp in the format of datetime.now()
        :param p1: int representing measurement of power1
        :param p2: int representing measurement of power2
        :param p3: int representing measurement of power3
        :param p4: int representing measurement of power4
        :param vrms: int representing measurement of vrms
        :param temperature: int representing measurement of temperature
        :return:
        """
        # the id of the record which will be stored in the database
        self.id = uuid.uuid4()

        # the UUID which represents the device itself
        self.deviceid = None
        self.type = 'power_measurement'

        # TODO standardize the measurements?
        self.ts = ts
        self.power1 = p1
        self.power2 = p2
        self.power3 = p3
        self.power4 = p4
        self.vrms = vrms
        self.temp = temperature

    def standardize(self, name, rate):
        """
        standardize the atr name by rate
        :param name:
        :param rate:
        :return:
        """
        if name in self.__dict__:
            if name =='power1':
                self.power1 = self.power1 * rate
            elif name =='power2':
                self.power2 = self.power2 * rate
            elif name =='power3':
                self.power3 = self.power3 * rate
            elif name =='power4':
                self.power4 = self.power4 * rate
            elif name == 'vrms':
                self.vrms = self.vrms * rate
            elif name =='temperature':
                self.temp = self.temp * rate
        else:
            raise AttributeError(name)

    def __str__(self):
        return """#type:power_measurement#ts:%s#device_id:%s#power1:%s#power2:
        %s#power3:%s#power4:%s#vrms:%s#temp:%s""" % (self.ts, self.deviceid, self.power1,
                                                     self.power2, self.power3, self.power4,
                                                     self.vrms, self.temp)
