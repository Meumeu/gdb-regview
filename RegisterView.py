from xml.etree.ElementTree import ElementTree
from os import path
import re
import pdb

from Register import Register


class RegisterView:
  def load_definitions(self, defs_file):
    self.tree = ElementTree()
    self.tree.parse(path.expanduser(defs_file))

    self.reg_defs = []
    for rg in self.tree.findall(".//registergroup"):
      # Create a full name for the register based on the register group if required
      # Some registers don't use the base/group name, so fall back to register name
      for r in rg.findall('./register'):
        try:
          fullname = rg.attrib['name'] + '_' + r.attrib['name'].split('_',1)[1]
        except:
          fullname = r.attrib['name']
        r.set('fullname',fullname)

        self.reg_defs.append(Register(r))

    print "Loaded register definitions:", path.expanduser(defs_file)

  def find_registers(self, reg_name):
    return filter(lambda x: x.get_fullname().startswith(reg_name), self.reg_defs)


  def find_registers_glob(self, reg_name):
    g = reg_name.replace("?", ".").replace("*", ".*")
    p = re.compile("^" + g + "$")
    return filter(lambda x: p.match(x.get_fullname()), self.reg_defs)


  def extract_bits(self, val, bit_len, bit_offset):
    return (val >> bit_offset) & ((1<<bit_len) - 1)


  def snapshot(self):
    self.snap = {}

    for reg in self.reg_defs:
      regstate = self.snap[reg.get_fullname()] = {}

      val = reg.get_val()

      for field in reg.get_elt().getchildren():
        bit_len    = int(field.attrib['bitlength'])
        bit_offset = int(field.attrib['bitoffset'])
        bit_name   = field.attrib['name']
        bit_val    = hex(self.extract_bits(val, bit_len, bit_offset))
        regstate[bit_name] = bit_val


  def diff_vs_snapshot(self):
    if (self.snap == None):
      print("please save snapshot first")
      return

    for reg in self.reg_defs:
      fullname = reg.get_fullname()
      if fullname not in self.snap:
        print("{} not in snapshot. skipping".format(fullname))
        continue

      regstate = self.snap[fullname]

      val  = reg.get_val()

      for field in reg.get_elt().getchildren():
        bit_name = field.attrib['name']
        if (bit_name not in regstate):
          print("field {}:{} missing from snapshot".format(fullname, bit_name))
          continue

        bit_len    = int(field.attrib['bitlength'])
        bit_offset = int(field.attrib['bitoffset'])

        bit_val    = hex(self.extract_bits(val, bit_len, bit_offset))
        if (regstate[bit_name] != bit_val):
          print("{}:{}  {}->{}".format(fullname, bit_name, regstate[bit_name], bit_val))
