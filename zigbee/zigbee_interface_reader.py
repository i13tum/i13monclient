from xbee import ZigBee
import serial

def open_zigbee_serialport(com_port='/dev/ttyUSB0', com_baud=9600):
    ser = serial.Serial(com_port, com_baud)
    xbee = ZigBee(ser)
    return xbee

