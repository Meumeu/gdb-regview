
import gdb
import struct

class Register:
    def __init__(self, elt):
        self.elt = elt


    def get_fullname(self):
        return self.elt.attrib['fullname']

    def get_address(self):
        return eval(self.elt.attrib['address'])

    def get_elt(self):
        return self.elt

    def get_val(self):
        addr = self.get_address()
        buff = gdb.inferiors()[0].read_memory(addr, 4)
        return struct.unpack("I", buff)[0]

    def extract_bits(self, val, bit_len, bit_offset):
        return (val >> bit_offset) & ((1<<bit_len) - 1)

    def __str__(self):
        val = self.get_val()
        retval = ["%s (*0x%08X) = 0x%08X" % (self.get_fullname(), self.get_address(), val)]
        reg = self.elt
        for field in reg.getchildren():
            bit_len     = int(field.attrib['bitlength'])
            bit_offset  = int(field.attrib['bitoffset'])
            bit_name    = field.attrib['name']
            description = field.attrib.get('description', 'no description')
            retval.append("\t%s\t0x%X\t\t%s" % (bit_name, self.extract_bits(val, bit_len, bit_offset), description))

        return "\n".join(retval)
