import gdb
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import RegisterView

rv = RegisterView.RegisterView()

class RegviewPrefixCommand (gdb.Command):
  "Prefix command for viewing special function registers."

  def __init__(self):
    super (RegviewPrefixCommand, self).__init__("regview",
        gdb.COMMAND_SUPPORT,
        gdb.COMPLETE_NONE, True)

class RegviewLoadCommand(gdb.Command):
  "Load register definitions from XML file."

  def __init__(self):
    super (RegviewLoadCommand, self).__init__ ("regview load",
      gdb.COMMAND_SUPPORT,
      gdb.COMPLETE_FILENAME)

  def invoke(self, arg, from_tty):
    rv.load_definitions(arg)

class RegviewLoadSvdCommand(gdb.Command):
  "Load register definitions from SVD XML file."

  def __init__(self):
    super (RegviewLoadSvdCommand, self).__init__ ("regview loadsvd",
      gdb.COMMAND_SUPPORT,
      gdb.COMPLETE_FILENAME)

  def invoke(self, arg, from_tty):
    rv.load_svd_definitions(arg)

class RegviewShowCommand(gdb.Command):
  "Show the value of a register."

  def __init__(self):
    super (RegviewShowCommand, self).__init__ ("regview show",
      gdb.COMMAND_SUPPORT)

  def invoke(self, arg, from_tty):
    e = rv.get_reg_element(arg)
    if e is None:
      print "Unknown register %s" % arg
      return
    addr = rv.get_reg_address(arg)
    buff = gdb.inferiors()[0].read_memory(addr, 4)
    val = struct.unpack("I", buff)[0]
    rv.print_reg(arg, val)

  def complete(self, arg, from_tty):
    return rv.find_registers(arg)

RegviewPrefixCommand()
RegviewLoadCommand()
RegviewLoadSvdCommand()
RegviewShowCommand()

if __name__ == '__main__':
  print 'Loaded', __file__
  print 'Type "regview <tab>" to see available commands.'
