_BROAD_CAST_ADDR = b'\xff\xfe'
_BROAD_CAST_LONG_ADDR = b'\x00\x00\x00\x00\x00\x00\xFF\xFF'


def switch_on_zigbee_device(xbee, dest_addr, dest_addr_long):
    xbee.tx(dest_addr=dest_addr, dest_addr_long=dest_addr_long, data=b'SET POW=ON\n')

def setup_zigbee_device(xbee, dest_addr, dest_addr_long):
    xbee.tx(dest_addr=dest_addr, dest_addr_long=dest_addr_long, data=b'SET POW=ON\n')
    xbee.tx(dest_addr=dest_addr, dest_addr_long=dest_addr_long, data=b'SET TXT=4\n')
    xbee.tx(dest_addr=dest_addr, dest_addr_long=dest_addr_long, data=b'SET RGB=off,off,on\n')

def initial_setup(xbee):
    setup_zigbee_device(xbee, _BROAD_CAST_ADDR, _BROAD_CAST_LONG_ADDR)