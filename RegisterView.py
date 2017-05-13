import xml.etree.ElementTree as ElementTree
import copy
#from xml.etree.ElementTree import ElementTree
from os import path

# This is just here for reference...
#
#  def print_reg(self, name, val):
#    print "%s (*0x%08X) = 0x%08X\n" % (name, self.get_reg_address(name), val)
#    reg = self.get_reg_element(name)
#    for field in reg.getchildren():
#      bit_len = int(field.attrib['bitlength'])
#      bit_offset = int(field.attrib['bitoffset'])
#      bit_name = field.attrib['name']
#      description = field.attrib.get('description', 'no description')
#      print "%s\t0x%X\t\t%s" % (bit_name, self.extract_bits(val, bit_len, bit_offset), description)
#
# set('name', value) sets an attribute
# SubElement(parent, tag, attrrib={}, **extra) adds sub element to parent

class RegisterView:
  
  def adapt_elements_to_peripheral(self, elements, new_peripheral_name, new_base_address):
    new_elements = copy.deepcopy(elements) 
    for r in new_elements.findall('.//register'):
      register_name = r.find('name').text
      fullname = new_peripheral_name + '_' + register_name
      r.set('fullname', fullname) 
      print "d   %s" %(fullname)
      # Calculate absolute address
      offset = r.find('addressOffset').text 
      r.set('address', hex(int(new_base_address,16) + int(offset,16)))
   
    return new_elements
 
  def load_svd_definitions(self, svd_file):
    self.tree = ElementTree.ElementTree()
    self.tree.parse(path.expanduser(svd_file))

    # Parse the svd defs into eclipse format 
    peripherals = self.tree.findall('.//peripheral')

    for peripheral in peripherals:
      peripheral_name = peripheral.find('name').text
      base_address = peripheral.find('baseAddress').text
      print "peripheral name = %s" %(peripheral_name)
      try:
        derived_from = peripheral.attrib['derivedFrom']
        elements = filter(lambda x: x.attrib['fullname'] == derived_from, self.tree.findall('.//peripheral'))
        if len(elements) <= 0:
          error_msg = "ERROR could not find peripheral %s info derived from %s" %(peripheral_name, derived_from)
          raise Exception(error_msg)

        # Create a duplicate in this peripheral
        print "derived!!"
        new_elements = adapt_elements_to_peripherals(self, elements, peripheral_name, base_address)
        peripheral.insert(new_elements)
        
        # No need to do anything else for this peripheral
        continue

      except KeyError:
        # Not derived from anything... proceed
        pass

      for r in peripheral.findall('.//register'):
        register_name = r.find('name').text
        fullname = peripheral_name + '_' + register_name
        r.set('fullname', fullname) 
        print "   %s" %(fullname)
        
        # Calculate absolute address
        offset = r.find('addressOffset').text 
        r.set('address', hex(int(base_address,16) + int(offset,16)))
      
        for f in r.findall('.//field'):
          new_attribs = {'bitlength':f.find('bitWidth').text,
                         'bitoffset':f.find('bitOffset').text,
                         'name':f.find('name').text,
                         'description':f.find('description').text};

          # Shove it back into the tree 
          ElementTree.SubElement(r, 'field', new_attribs);

    self.reg_defs = self.tree.getiterator('register')

  def load_definitions(self, defs_file):
    self.tree = ElementTree.ElementTree()
    self.tree.parse(path.expanduser(defs_file))
    reggroups = self.tree.findall(".//registergroup")
    for rg in reggroups:
      # Create a full name for the register based on the register group if required
      # Some registers don't use the base/group name, so fall back to register name
      for r in rg.findall('./register'):
        try:
          fullname = rg.attrib['name'] + '_' + r.attrib['name'].split('_',1)[1]
        except:
          fullname = r.attrib['name']
        r.set('fullname',fullname)

    self.reg_defs = self.tree.getiterator('register')
    print "Loaded register definitions:", path.expanduser(defs_file)

  def find_registers(self, reg_name):
    regs = filter(lambda x: x.attrib['fullname'].startswith(reg_name), self.reg_defs)
    return map(lambda x: x.attrib['fullname'], regs)

  def get_reg_element(self, reg_name):
    elems = filter(lambda x: x.attrib['fullname'] == reg_name, self.reg_defs)
    if len(elems) > 0:
      return elems[0]
    else:
      return None

  def extract_bits(self, val, bit_len, bit_offset):
    return (val >> bit_offset) & ((1<<bit_len) - 1)

  def get_reg_address(self, name):
    return eval(self.get_reg_element(name).attrib['address'])

  def print_reg(self, name, val):
    print "%s (*0x%08X) = 0x%08X\n" % (name, self.get_reg_address(name), val)
    reg = self.get_reg_element(name)
    for field in reg.getchildren():
      bit_len = int(field.attrib['bitlength'])
      bit_offset = int(field.attrib['bitoffset'])
      bit_name = field.attrib['name']
      description = field.attrib.get('description', 'no description')
      print "%s\t0x%X\t\t%s" % (bit_name, self.extract_bits(val, bit_len, bit_offset), description)

