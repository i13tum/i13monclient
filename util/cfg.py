import configparser

def _get_config():
    config = configparser.ConfigParser()
    config.read('client.config')
    return config


def _get_zigbee_config():
    return _get_config()['zigbee']


def get_plugmeters():
    return _get_config()['zigbee']['plugmeters'].split(';')


def get_multisensors():
    return _get_zigbee_config()['multisensors'].split(';')

def get_rfpi_settings():
    return _get_config()['rfpi']

def get_ssl_settings():
    return _get_config()['ssl']


def get_config():
    return _get_config()

def get_decoder_info(node_type):
    return _get_config()[node_type]

def _get_server_info():
    return _get_config()['serverinfo']

def get_server_host():
    return _get_server_info()['serverhost']


def get_server_port():
    return _get_server_info()['serverPort']
