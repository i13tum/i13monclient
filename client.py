import logging
import communication

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, communication_module):
        self._communication_module = communication_module
        self._process = None

    def create_commincation_moduel(self, node_decoder):
            communication_module = communication.CommunicationModule(server_adr, server_port, node_decoder, ssl_dict)
            return Client(communication_module)
