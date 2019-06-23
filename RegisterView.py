import xml.etree.ElementTree as ElementTree
import copy
from os import path
import re
import pdb

from Register import Register



class RegisterView:
  
  def adapt_elements_to_peripheral(self, elements, new_peripheral_name, new_base_address):
    new_elements = copy.deepcopy(elements) 
    
    for r in new_elements.findall('.//register'):
      register_name = r.find('name').text
      fullname = new_peripheral_name + '_' + register_name
      r.set('fullname', fullname) 
      # Calculate absolute address
      offset = r.find('addressOffset').text 
      hex_base = 16
      new_address = int(new_base_address, hex_base) + int(offset, hex_base)
      r.set('address', hex(new_address))
   
    return new_elements

  def parse_svd_peripheral(self, peripheral, peripherals):
    peripheral_name = peripheral.find('name').text
    base_address = peripheral.find('baseAddress').text
    try:
      derived_from = peripheral.attrib['derivedFrom']
      derive_matches = list(filter(lambda x: x.find('name').text == derived_from, peripherals))
      if len(derive_matches) <= 0:
        error_msg = "ERROR could not find peripheral %s info derived from %s" %(peripheral_name, derived_from)
        raise Exception(error_msg)

      # Create a duplicate in this peripheral
      new_elements = self.adapt_elements_to_peripheral(derive_matches[0], peripheral_name, base_address)
      peripheral.insert(0, new_elements)
        
      # No need to do anything else - complete copy has been made
      return 

    except KeyError:
      # Not derived from anything... proceed
      pass

    for r in peripheral.findall('.//register'):
      register_name = r.find('name').text
      fullname = peripheral_name + '_' + register_name
      r.set('fullname', fullname) 
        
      # Calculate absolute address
      offset = r.find('addressOffset').text 
      hex_base = 16
      address = int(base_address, hex_base) + int(offset, hex_base)
      r.set('address', hex(address))
      
      for f in r.findall('.//field'):

        # Add as a child of the register 
        adapted_field = ElementTree.Element("field")

        adapted_field.attrib['bitlength'] = f.find('bitWidth').text
        adapted_field.attrib['bitoffset'] = f.find('bitOffset').text
        adapted_field.attrib['name'] = f.find('name').text
        adapted_field.attrib['description'] = f.find('description').text.replace("\n              ", "")

        r.insert(0, adapted_field)
 
  def load_svd_definitions(self, svd_file):
    self.tree = ElementTree.ElementTree()
    self.tree.parse(path.expanduser(svd_file))

    # Parse the svd defs into eclipse format 
    peripherals = self.tree.findall('.//peripheral')

    for peripheral in peripherals:
      self.parse_svd_peripheral(peripheral, peripherals)

    #self.reg_defs = self.tree.getiterator('register')
    self.reg_defs = []
    for i in self.tree.getiterator('register'):
        self.reg_defs.append(Register(i))
    print("Loaded register definitions from SVD:", path.expanduser(svd_file))

  def load_definitions(self, defs_file):
    self.tree = ElementTree.ElementTree()
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

    print("Loaded register definitions:", path.expanduser(defs_file))

  def find_registers(self, reg_name):
    return list(filter(lambda x: x.get_fullname().startswith(reg_name), self.reg_defs))


  def find_registers_glob(self, reg_name):
    g = reg_name.replace("?", ".").replace("*", ".*")
    p = re.compile("^" + g + "$")
    return list(filter(lambda x: p.match(x.get_fullname()), self.reg_defs))


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
