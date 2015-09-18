import multiprocessing

from communication.communication import create_ssl_context, CommunicationModule
from rfpi.decoder import create_decoder
from rfpi.interface_reader import RFPi
from util import cfg
from util.cfg import get_rfpi_settings, get_ssl_settings
from util.logger_factory import setup_logging
from zigbee.zigbee_client import ZigBeeReader
from communication.reporter import Reporter


def get_zigbee_config():
    """
    Read from the configuration all configured multisensors and plugmeters and returns a dictionary with the mappings

    :return: dictionary[string, string]
    """
    cd = dict()
    for ms in cfg.get_multisensors():
        cd.update({ms.strip(): 'multisensor'})
    for pm in cfg.get_plugmeters():
        cd.update({pm.strip(): 'plugmeter'})

    return cd


if __name__ == '__main__':
    setup_logging()

    queue = multiprocessing.Queue(maxsize=0)

    rfpi = RFPi(queue, create_decoder(), get_rfpi_settings()['port'], get_rfpi_settings()['baud'])
    xbeereader = ZigBeeReader(queue, get_zigbee_config())

    sslctx = create_ssl_context(get_ssl_settings())

    cm = CommunicationModule(cfg.get_server_host(), cfg.get_server_port(), sslctx)
    reporter = Reporter(queue, cm)

    rfpi.set_up()
    rfpi.start()

    xbeereader.set_up()
    xbeereader.start()

    reporter.run()
