from datetime import datetime
import logging
import multiprocessing
from pickle import dump
import time
from dto.zigbeedatatypes import Plugmeasurement
from zigbee.zigbee_interface_reader import open_zigbee_serialport
from util import zigbeeconfig

logger = logging.getLogger(__name__)


class ZigBeeReader(multiprocessing.Process):
    def __init__(self, queue, devicemapping):
        multiprocessing.Process.__init__(self, daemon=True)

        self.queue = queue
        self.devicemapping = devicemapping

    def mac_address_to_str(self, mac):
        return ':'.join("{:02X}".format(c) for c in mac)

    def parse_plugmeasurement(self, ts, mac_adress, resp):
        pms = Plugmeasurement(ts, mac_adress)
        for item in resp['rf_data'].decode('utf-8').split('\n'):
            if '=' in item:
                k, valv = item.split('=')
                if k == 'POW':
                    pms.pow = valv
                elif k == 'FREQ':
                    pms.freq = float(valv.split('Hz')[0])
                elif k == 'VRMS':
                    pms.vrms = int(valv.split('V')[0])
                elif k == 'LOAD':
                    pms.load = int(valv.split('W')[0])
                elif k == 'WORK':
                    pms.work = float(valv.split('kWh')[0])
                elif k == 'IRMS':
                    pms.irms = int(valv.split('mA')[0])

        return pms

    def parse_response(self, resp, count):
        try:
            source = self.mac_address_to_str(resp['source_addr_long'])
            parser = self.devicemapping.get(source)
            logger.debug("#debug:start-parsing#from:%s#count:%s" % (source, count))
            if parser == 'plugmeter':
                return self.parse_plugmeasurement(datetime.now(), source, resp)
            elif parser == 'multisensor':
                logger.warn("#warn:no-multisensor")
            else:
                logger.warn("#warn:unregistered-device#id:%s" % source)
        except KeyError:
            logger.error("#erorr:-unknown-msg-read %s " % resp)
        except:
            logger.error("#error:dumping-res#cnt:%s" % count)
            dump(resp, open("error-%s.p" % count, "wb"))

    def set_up(self):
        self.zigbee = open_zigbee_serialport()
        logger.debug("#debug:setting-up-all-zigbee-devices")
        zigbeeconfig.initial_setup(self.zigbee)

    def run(self):
        count = 0
        while True:
            count = count + 1
            try:
                response = self.zigbee.wait_read_frame()
                parsed = self.parse_response(response, count)
                self.queue.put(parsed)
                logger.debug("#debug:read-msg-from-zigbee")
            except Exception as e:
                logger.error("#error:while-reading-from-Zigbee")
                time.sleep(0.5)
                self.run()
