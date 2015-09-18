import logging
import asyncio
import pickle
import ssl

from message_types import measurement_msg

_logger = logging.getLogger(__name__)


def create_ssl_context(ssl_dict):
    """
        loads the ssl certificate for secure communication
        :param ssl_dict: dictionary consisting of certification file, key
        keys: certFile, keyFile
        :returns ssl.SSLContext
        """
    _logger.debug("#debug:loading-ssl-certificates")
    try:
        # choosing the version of the SSL Protocol
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ssl_context.options |= ssl.OP_NO_SSLv2
        ssl_context.options |= ssl.OP_NO_SSLv3
        ssl_context.load_cert_chain(certfile=ssl_dict["certFile"], keyfile=ssl_dict["keyFile"])
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.check_hostname = False
        _logger.info("#info:ssl-certificates-loaded!")
        return ssl_context

    except ssl.SSLError as e:
        _logger.exception(e)
        _logger.error("#error:could-not-load-the-ssl-certificates")
        raise e


class CommunicationModule():
    """
    This class is responsible for handling communications with Server

    _to_be_acknowledged: is a dictionary, where keys are message_id and values
    are the message itself, which is a list of dictionaries, each dictionary represents
    a measurement

    _to_be_sent: which is a list of dictionaries, each dictionary represents
    a measurement
    """

    def __init__(self, server_host, server_port, ssl_context):
        self._server_host = server_host
        self._server_port = server_port
        self._ssl_context = ssl_context
        self._reader = None
        self._writer = None

        # dictionary of Messages which
        # have not been acknowledged
        self._to_be_acknowledged = {}

        # the length of each message, number of
        #  measurements to be send together
        self._WINDOW_SIZE = 3

        # the message that will be sent to the server
        # a list of measurements, size : _WINDOW_SIZE
        # each time this list is reach to its limit, a
        # message will be sent and list will be emptied
        self._to_be_sent = []

        # giving ids to the messages
        self._MSG_COUNTER = 0

    @asyncio.coroutine
    def connect(self):
        # get a connection
        try:
            self._reader, self._writer = yield from \
                asyncio.open_connection(
                    self._server_host, self._server_port,
                    ssl=self._ssl_context)
        except Exception as e:
            _logger.exception(e)

            # the exception will be handled on
            #  the next level (report method of
            #  the reporter class)
            raise e

    @asyncio.coroutine
    def send(self, msg):
        """
        called by Reporter
        sends the measurement alongside the previously buffered messages if the limit (_WINDOW_SIZE)
        has been reached(by calling send_message), otherwise appends it to the buffered list (to_be_sent)
        :param msg: an instance of an object representing a measurement
        """
        try:

            msg = msg.__dict__
            self._to_be_sent.append(msg)

            # check if the _message can be send
            if len(self._to_be_sent) >= self._WINDOW_SIZE:

                # getting the first _WinDOW_SIZE items
                message = self._to_be_sent[0:self._WINDOW_SIZE]

                # creating the message, giving a new id
                # to the message, and send it to the server
                self._MSG_COUNTER += 1
                yield from self.send_measurement(self._MSG_COUNTER, message)
                response = yield from self.receive_message(self._MSG_COUNTER)

                # adding the message to the to_be_acknowledged dictionary
                self._to_be_acknowledged[self._MSG_COUNTER] = message

                # removing message from _to_be_sent list
                self._to_be_sent = self._to_be_sent[self._WINDOW_SIZE:]

                if response:
                    yield from self.handle_response(response)
                else:
                    _logger.warn("#warn:no-ack-received-from-server-for-msg-%s" % self._MSG_COUNTER)
            else:
                _logger.debug("#debug:msg-will-be-send-later-len(to_be_sent):%s" % len(self._to_be_sent))

        except Exception as e:
            _logger.error("#error:error-occurred-while-sending-the-message:%s" % msg)
            _logger.exception(e)

            # to be handled by the upper class Reporter
            raise e

    @asyncio.coroutine
    def send_measurement(self, msg_id, msg):
        """
        sends a list of measurements
        :param msg_id: int
        :param msg: list of dictionaries
        :return:
        """
        message = measurement_msg.MeasurementMessage(id=msg_id, data=msg)

        if msg:
            # when we are sending a measurement and msg is not None
            _logger.debug('#debug:sending-message-with-id-:%s-and-size:%s' % (msg_id, len(msg)))

        yield from self.send_message(message)

    @asyncio.coroutine
    def receive_message(self, msg_id):
        """
        waits to receive response by the other side
        :param msg_id: int , the msg we are waiting for its response
        :return: (bytes) response sent by server
        """
        try:
            data = yield from asyncio.wait_for(self._reader.read(1000), timeout=3)
            return data

        except asyncio.TimeoutError:
            _logger.warn("#warn:timeout-reached-while-waiting-for-ack-msg:%s" % msg_id)

    @asyncio.coroutine
    def send_message(self, message):
        """
        Sends a message to the server
        :param msg_id: (int) id of the message
        :param message: an inherited instance of GeneralMessage
        (@see general_message.GeneralMessage)
        """
        # packing the message into bytes
        byte_message = pickle.dumps(message)

        # sending the message to the server
        self._writer.write(byte_message)
        yield from self._writer.drain()

    @asyncio.coroutine
    def handle_response(self, message):
        """
        handles a message sent by the server
        :param message: (bytes)
        :return:
        """
        try:
            message = pickle.loads(message)

            # message must be a subclass of GeneralMessage
            _logger.debug("received-msg-of-type-%s: " % message.get_type())

            if message.get_type() == 'ack':
                yield from self.handle_ack(message)
            elif message.get_type() == 'request':
                yield from self.handle_request(message)
            else:
                _logger.warn("#warn:unknown-message-type-received:%s" % message.get_type())
        except pickle.PickleError:
            _logger.error("#error:Pickling-error-while-analyzing-message:%s" % message)
        except KeyError:
            _logger.warn("#debug:-corrupted-message-received-%s" % message)
        except AttributeError:
            _logger.error("#error:message-is-corrupted-%s" % message)

    @asyncio.coroutine
    def handle_ack(self, ack):
        """
        analyzes the acknowledgment sent by the server
        :param ack: an instance of type AckknowledgmentMessage
        :return:
        """
        try:
            _logger.debug("#debug:ack:%s" % ack)

            # checking and removing the delivered message from
            #  our waiting list
            if ack.get_success() in self._to_be_acknowledged:
                self._to_be_acknowledged.pop(ack.get_success())
            else:
                _logger.warn("#debug:acknowledgment-received-for-non-existing-message-id:%s" % ack.get_success())
                _logger.debug("#debug:to_be_acknowledged-list:%s" % self._to_be_acknowledged)

            # if the server asked for a specific
            # msg id send the wanted message
            if ack.get_wanted():

                # send the msg if we have it in buffer
                if ack.get_wanted() in self._to_be_acknowledged:

                    # sending the message to the server
                    _logger.debug("#debug:sending-wanted-message-id: %s" % ack.get_wanted())
                    yield from self.send_measurement(ack.get_wanted(), self._to_be_acknowledged[ack.get_wanted()])
                    response = yield from self.receive_message(ack.get_wanted)
                    yield from self.handle_response(response)

                # the msg asked by server does not exists
                # in buffer
                else:
                    _logger.warn("#debug:acknowledgment-received-for-non-existing-message-id:%s" % ack.get_wanted())
                    _logger.debug("#debug:to_be_acknowledged-list:%s" % self._to_be_acknowledged)

                    # sending None for this message_id
                    # server will stop requesting for this id
                    yield from self.send_measurement(ack.get_wanted(), None)

        except pickle.PickleError:
            _logger.error("#error:Pickleing-error-while-analyzing-ack:%s" % ack)
        except KeyError:
            _logger.warn("#debug:-corrupted-ack-received-%s" % ack)

    @asyncio.coroutine
    def handle_request(self, msg):
        """
        handles a request for getting message counter of the client by
        the server, sends the server the news value for the _MSG_COUNTER
        :param msg: an instance of type requests.Request message type
        :return:
        """

        if msg.get_request() == 'GET_MSG_COUNTER':
            msg.set_response(self._MSG_COUNTER)
            yield from self.send_message(msg)

    def disconnect(self):
        _logger.info("#info:disconnecting-the-communication-module...")
        self._writer.close()
