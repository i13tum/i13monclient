from datetime import datetime
import logging
import uuid
from dto import rfdatatypes
from util import cfg
import struct
from dto import temphdatatypes

_logger = logging.getLogger(__name__)

def create_decoder():
    """
    creates a decoder for decoding data frames
    :return: (Decoder) an instance of the Decoder
    """

    # create a NodeDecoder for 'node10'
    decodes = get_decoding_info('node10')
    node_10_decoder = Node10Decoder(decodes, 10)

    # create a NodeDecoder for 'temp-hum'
    decodes = get_decoding_info('temp-hum')
    temp_hum_decoder = TempHumDecoder(decodes, None)

    # create the Decoder
    node_decoder = Decoder(node_10_decoder, temp_hum_decoder)
    return node_decoder


def get_decoding_info(node_type):
    """
    :param node_type: a string representing type of the node which we want to
     decode its data frame. Look into config file: client.config!
    :return (tuple) decoding_info:
    # decoding_info is a tuple containing information in config file
    # the tuple is consist of a dictionary and a list
    # the dictionary is formatting structure and the deviceid. The list is consist
    # of measurements values which is available in the data frame, which is read
    # from the respected node
    # example: _node_decodes = ({'rec_data_format':
    # '<BBBBBBBBBBBB', 'real_data_format': '<hhhhhh'},
    # ['power1', 'power2', 'power3', 'power4', 'vrms', 'temp'])
    """

    values = {}
    value_list = []

    # get the section related to decoding node: node_type
    config = cfg.get_decoder_info(node_type)
    for option in config.keys():

        # if it is a single string add it to
        # List of measurements
        if len(config.get(option)) < 1:
            value_list.append(option)
        else:

            # add it to formatting structure dictionary
            values[option] = config.get(option)

    decoding_info = (values, value_list)
    return decoding_info

class Decoder:
    """
    This Class is the General Decoder used by interface_reader
    it has instances of NodeDecoders for decoding
    the data frames
    """
    def __init__(self, node10_decoder, temp_hum_decoder):
        self._node10_decoder = node10_decoder
        self._temp_hum_decoder = temp_hum_decoder

    def decode(self, data):
        """
        decodes data based on the node_id included in the data
        :param data: (string) the data frame passed by RFPi
        :return: the object of the specified node_id by the data information
        """

        # get an array of the strings from the line
        # read from the serial port (RFPi)
        data = data.split(' ')

        # converting strings/chars values of numbers to int
        try:
            # checking and discarding inputs which are not measurements!
            for i in range(len(data)):
                if data[i].isdigit():
                    data[i] = int(data[i])
                else:
                    # unable to decode! non integer found!
                    _logger.warn('#warn:corrupted-data-unable-to-decode:data:%s' % data)
                    return None
        except Exception as e:
            _logger.error("#error:in-converting-data[%s]-to-int-data:-%s" % (i, data))
            _logger.exception(e)
            return None

        # get and remove the node_id
        # from data
        node_id = data[0]
        data = data[1:]

        # decode the data
        try:
            if node_id == 10:
                return self._node10_decoder.decode(data)

            elif node_id == 19 or node_id == 22 or node_id == 23 or node_id == 24:

                # first set the node_id for temp_hum decoder then decode
                self._temp_hum_decoder.set_id(node_id)
                return self._temp_hum_decoder.decode(data)

            else:
                _logger.info("#missing-decoder:%s" % node_id)

        except struct.error as e:
            _logger.error("#error:in-decoding-!-%s" % data)
            _logger.exception(e)
            return None


class NodeDecoder():
    def __init__(self, info_dict, node_id):
        """
        :param info_dict : @see get_decoding_info function!
        """

        self._node_decodes = info_dict
        self._node_id = node_id

    def decode(self, data):
        """
        to be implemented in inherited class
        :param data:
        :return:
        """
        pass


class Node10Decoder(NodeDecoder):
    def decode(self, data):
        """
        decodes data for node10
        :param data: (array of string) the data frame passed by RFPi
        ,which the data[0] (representing node id)is excluded
        :return: the object of the PowerMeasurement
        """
        try:
            # interpret each two bytes as a singe integer
            result = struct.pack(self._node_decodes[0]['rec_data_format'], *data)
            result = struct.unpack(self._node_decodes[0]['real_data_format'], result)

            node = rfdatatypes.PowerMeasurement(datetime.now(), *result)

            # in order to making the measurements standard
            node.standardize('vrms', 0.01)

            # get the deviceid from the node_decodes dictionary
            # convert it to uuid format!
            node.deviceid = uuid.UUID(self._node_decodes[0][str(self._node_id)])
            return node
        except AttributeError as e:
            _logger.warn("#warn:%s:is-not-an-attribute-of-rfdatatypes")
            _logger.exception(e)


class TempHumDecoder(NodeDecoder):

    def set_id(self, id):
        self._node_id = id

    def decode(self, data):
        """
        decodes data for temperature humidity sensors
        :param data: (array of string) the data frame passed by RFPi
        ,which the data[0] (representing node id)is excluded
        :return: the object of the TempHumidityMeasurements
        """
        try:
            # interpret each two bytes as a singe integer
            result = struct.pack(self._node_decodes[0]['rec_data_format'], *data)
            result = struct.unpack(self._node_decodes[0]['real_data_format'], result)

            node = temphdatatypes.TempHumidityMeasurements(datetime.now(), *result)

            # in order to making the measurements standard
            node.standardize('all', 0.1)

            # get the deviceid from the node_decodes dictionary
            # convert it to uuid format!
            node.deviceid = uuid.UUID(self._node_decodes[0][str(self._node_id)])
            return node
        except AttributeError as e:
            _logger.warn("#warn:%s:is-not-an-attribute-of-temp-hum")
            _logger.exception(e)


if __name__ == '__main__':
    #Some testing

    decoder = create_decoder()
    data1 = "23 225 0 0 0 7 1 30 0"
    data2 = "10 4 0 0 0 0 0 0 0 42 98 0 0"
    n1 =decoder.decode(data1)
    n2 = decoder.decode(data2)
    print(n1)
    print(n2)
