import logging


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    formatter = logging.Formatter('#ts:%(asctime)s#level:%(levelname)s#name:%(name)s%(message)s')

    err_handler = logging.FileHandler('errorlog-client.log', mode='w', delay=True)
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)

    logging.getLogger('').addHandler(err_handler)

    fh = logging.FileHandler('client.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logging.getLogger('').addHandler(fh)