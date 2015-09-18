import logging
import serial
import multiprocessing

_logger = logging.getLogger(__name__)

class RFPi(multiprocessing.Process):
    """
    This Class is responsible for reading data from the
    serial Port on Raspberry Pi
    """
    def __init__(self, queue, decoder, com_port, com_baud):
        """
        :param queue: (multiprocessing.Queue) a shared queue shared with Reporter
        :param decoder: an instance of a Decoder
        :param com_port: (string): path to COM port
        :param com_baud: (int)
        :return:
        """
        multiprocessing.Process.__init__(self, daemon=True)
        self._com_port = com_port
        self._com_baud = com_baud
        self._queue = queue
        self.decoder = decoder
        self.serial_port = None
        self._defaults = {'pause': 'off', 'interval': 0, 'datacode': '0', 'timestamped': 'False'}
        self._jee_settings = {'baseid': '15', 'frequency': '433', 'group': '210', 'quiet': 'True'}
        self._jee_prefix = ({'baseid': 'i', 'frequency': '', 'group': 'g', 'quiet': 'q'})

    def makeset(self, setting, value):
        """
        writes a single setting into the device
        :param setting: (string) key of the setting dictionary (a property)
        :param value: (string) value of the property
        :return:
        """

        # if value is a string representing a boolean
        #  converts it to an integer
        if str.capitalize(str(value)) in ['True', 'False']:
            value = int(value == 'True')

        # append 'i','b','g', or 'q' to the value
        # for settings 'basedid', 'frequency', 'group', 'quiet'
        # and convert value to bytes in order to be written into serial
        if setting == 'baseid':
            command = (value + 'i').encode('ascii')
        elif setting == 'frequency' and value in ['433', '868', '915']:
            command = ('%sb' % value[1:]).encode('ascii')
        elif setting == 'group' and 0 <= int(value) <= 212:
            command = ('%sg' % value).encode('ascii')
        elif setting == 'quiet' and 0 <= int(value) < 2:
            command = ('%sq' % str(value)).encode('ascii')
        try:
            if command:

                # write the setting into the device
                _logger.info("#info:start-writing-setting#command:%s" % command)
                self.serial_port.write(command)
            else:
                _logger.info("#info:empty-command")
        except serial.SerialException as e:
            _logger.exception(e)
            _logger.error("could not set the " + command + " for", self.serial_port, str(e.args))

    def set_up(self, settings=None):
        """
        sets up the device using setting_dict
        :param ser: (serial.Serial)
        :param setting_dict: dictionary of settings
        """

        # open a Serial.serial port
        self.serial_port = self.open_serial_port(self._com_port, self._com_baud)

        # setup the device, if no setting
        # is available use _jee_settings
        if settings is None:
            settings = self._jee_settings
        for setting, value in settings.items():
            self.makeset(setting, value)

    @staticmethod
    def open_serial_port(com_port="/dev/ttyAMA0", com_baud=9600):

        """
        opens a serial port
        :param com_port: (string): path to COM port
        :param com_baud: (int)
        :return: (Serial.serial)
        """
        return serial.Serial(com_port, com_baud)

    def run(self):
        """
        runs the Process for reading from serial port
        :return:
        """

        _logger.info("#info:reading from the serial port %s" % str(self.serial_port))
        if self.serial_port:

            # line is the input we get form serial port
            line = ""
            try:
                while True:
                    while "\r\n" not in line:

                        # keep reading/appending till we reach to a '\r\n'
                        line += self.serial_port.readline().decode("ascii")

                    # To get rid of the '\r\n', which has a size 2 !
                    # When there is no more data to read from serial port
                    # we may have a line containing just a '\r\n'!
                    line = line.strip()
                    if len(line) > 0:

                        _logger.debug("#nextline:%s", line)

                        # decode the line
                        data = self.decoder.decode(line)

                        # if decode was successful put into shared queue
                        if data:
                            self._queue.put_nowait(data)

                        # empty the line after each successful read
                        line = ""

            except serial.SerialException as e:
                _logger.error("#error:An-error-occurred-while-reading-from-the-serial-port")
                _logger.exception(e)
            except Exception as e:
                _logger.error("#error:UNpredicted-exception-while-reading-from-serial-port")
                _logger.exception(e)
                self.run()
        else:
            _logger.error("#error:Serial-port-is-None!-Call-set_up-function?")
