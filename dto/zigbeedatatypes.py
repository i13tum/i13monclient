import uuid

class Plugmeasurement:
    """
    For Piccerton plug meters
    """
    def __init__(self, ts, mac_address):
        # The id of the record which will be stored in the database
        self.id = uuid.uuid4()
        self.type = 'plug_measurement'

        # The Mac Address which represents the device itself
        self.mac_address = mac_address
        self.ts = ts
        self.load = None
        self.irms = None
        self.vrms = None
        self.freq = None
        self.pow = None
        self.work = None

    def __str__(self):
        return "#type:plug_measurement#ts:%s#mac_address:%s#load:%s#irms:%s#vrms:%s#freq:%s#pow:%s#work:%s" % (self.ts, self.mac_address, self.load, self.irms, self.vrms, self.freq, self.pow, self.work)