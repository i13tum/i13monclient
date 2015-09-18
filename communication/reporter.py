import logging
import asyncio
import pickle
import queue
import time

_logger = logging.getLogger(__name__)

_RECONNECT_TIMEOUT = 10
_RIGHT_TO_FILE_TIME = 5
_BUFFERED_READ_HICCUP = 0.5
_EMPTY_QUEUE_HICCUP = 1


class Reporter():
    """
    this class is responsible for passing the measurements
    to the communication module and buffer data whenever
    the connection is stopped
    """

    def __init__(self, shared_queue, communication_module):
        """
        :param shared_queue: a queue which is filled by a sensor (Zigbee/interface) reader
        :param communication_module: an instance of CommunicationModule
        :return:
        """
        self._queue = shared_queue
        self._communication_module = communication_module

        # queue to retrieve buffered data from the file
        self._buffered_queue = None

        # asyncio loop
        self._loop = None

    @asyncio.coroutine
    def report(self):

        # message to be reported
        # which is an object representing a measurement
        msg = None
        try:

            # get a connection
            yield from self._communication_module.connect()

            # check if buffered queue is empty and needs to be filled
            # replace the empty buffered queue with the buffered data from the file
            if self._buffered_queue is None or self._buffered_queue.empty():
                _logger.debug("#debug:filling-the-buffered-queue")
                self._buffered_queue = Reporter.get_buffered_data()

            # append data from the file to the buffered queue if buffered queue is not empty
            elif not self._buffered_queue.empty():
                _logger.debug("#debug:appending-from-the-buffered-file-to-the-buffered-queue...")
                temp = Reporter.get_buffered_data()
                while not temp.empty():
                    self._buffered_queue.put(temp.get())

            _logger.debug("#debug:sending-buffered-data#qsize:%s" % self._buffered_queue.qsize())

            # try to send the data to the server
            while True:

                # first send the buffered data from the file
                while not self._buffered_queue.empty():
                    msg = self._buffered_queue.get()
                    if msg:
                        _logger.debug('#debug:sending-buffered-data#data:%s' % msg)
                        yield from self._communication_module.send(msg)
                        yield from asyncio.sleep(_BUFFERED_READ_HICCUP)

                # try to read form the shared queue and send
                # recently measurement data to the server
                while not self._queue.empty():
                    msg = self._queue.get()
                    if msg:
                        yield from self._communication_module.send(msg)
                yield from asyncio.sleep(_EMPTY_QUEUE_HICCUP)

        # connection has been lost
        except ConnectionResetError:
            _logger.warn("#warn:connection-lost!")

            # try to buffer data into a file while the connection is lost
            yield from self.write_to_file(_RECONNECT_TIMEOUT, msg)
            _logger.debug("#debug:reconnecting-after-connection-reset-error")

            # try to reconnect and start reporting again
            yield from self.report()

        # failed to connect to the server
        except ConnectionRefusedError:
            _logger.warn("#warn:could not connect to the server!")

            # try to buffer data into a file while there is no connection
            yield from self.write_to_file(_RECONNECT_TIMEOUT, msg)
            _logger.debug("#debug:reconnecting-after-connection-refused-error")

            # try to reconnect and start reporting again
            yield from self.report()

        # keyboard interrupt
        except KeyboardInterrupt:
            _logger.error("operation-interrupted-by-user!")
            return

        except Exception as e:
            _logger.error("#error:unpredicted-exception-occurred-while-communicating")
            _logger.exception(e)
            yield from asyncio.sleep(_RECONNECT_TIMEOUT)

            # try to reconnect and start reporting again
            _logger.debug("#debug:reconnecting-after-unpredicted-exception")
            yield from self.report()

    @asyncio.coroutine
    def write_to_file(self, seconds, failed_msg, file_name="buffered-data.p"):
        """
        it will write the data to a file for a period
        of 'seconds' seconds!
        used when the connection is lost to store the data locally
        and try to send them again when we have the connection back
        :param: seconds, time in seconds for this method to run
        :param: failed_msg, the last message which could not be send
        :return:
        """

        with open(file_name, 'ab+') as fout:

            # first write the failed message to the file
            if failed_msg:
                pickle.dump(failed_msg, fout)
                fout.flush()

            # calculate the time which this method should be run
            start_time = time.time()
            end_time = start_time + seconds

            # get data from the shared queue and buffer them into the file
            _logger.debug("#debug:writing-data-to-the-file")
            while time.time() < end_time:
                if not self._queue.empty():
                    try:
                        data = self._queue.get(timeout=0.500)  # ToDo Do we need a timeout?
                        if data:
                            pickle.dump(data, fout)
                            fout.flush()
                    except queue.Empty as e:
                        _logger.warn("#warn:time-out-reached!-could-not-get-from-the-shared-queue")

            _logger.debug("#debug:write_to_file-time-out-reached.-Exiting-the-method...")
            fout.close()

    @staticmethod
    def get_buffered_data(file_name="buffered-data.p"):
        """
        reads lines from buffered file and return a queue containing data
        :rtype : queue.Queue
        :param file_name:
        :return: queue containing data
        """
        _logger.info("#info:reading-from-buffered-file...")
        temp_queue = queue.Queue(maxsize=0)
        try:
            with open(file_name, 'rb+') as fin:
                try:
                    while True:
                        # read until end of file reached
                        data = pickle.load(fin)
                        temp_queue.put(data)
                except EOFError:
                    _logger.debug("#debug:reading-buffered-data-finished!#qsize:%s" % temp_queue.qsize())
                    fin.close()

            # emptying the file!
            # each time the buffered file is read,
            # it is being emptied in order not to read and
            # report the previously reported buffered data
            open(file_name, 'w').close()
            return temp_queue
        except FileNotFoundError as e:
            _logger.warn("#warn:file-%s-does-not-exists-" % file_name)
            return temp_queue

    def run(self):
        """
        run the reporter thread
        """
        self._loop = asyncio.get_event_loop()
        try:
            self._loop.run_until_complete(self.report())
        except KeyboardInterrupt:
            pass
        self._loop.close()

    def disconnect(self):
        self._communication_module.disconnect()
        self._loop.close()
