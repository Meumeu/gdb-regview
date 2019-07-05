# kate: space-indent on; indent-width 2; replace-tabs on
import gdb
import struct
import sys
import os
import pdb
import pprint

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import RegisterView
import I2C

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
    elts = rv.find_registers(arg)

    # if the user includes a ? or * in the argument, we expand them here.
    if (arg.find("?") != -1) or (arg.find("*") != -1):
      elts.extend(rv.find_registers_glob(arg))

    if len(elts) == 0:
      print("Unknown register %s" % arg)
      return

    for elt in elts:
      print(elt)

  def complete(self, arg, from_tty):
    return [reg.get_fullname() for reg in rv.find_registers(arg)]


class  RegviewSnapshotCommand(gdb.Command):
  "Take a snapshot of the current register state."

  def __init__(self):
    super (RegviewSnapshotCommand, self).__init__ ("regview snapshot",
      gdb.COMMAND_SUPPORT)

  def invoke(self, arg, from_tty):
    rv.snapshot()


class  RegviewSaveSnapshotCommand(gdb.Command):
  "Take a snapshot of the current register state and save it to a file."

  def __init__(self):
    super (RegviewSaveSnapshotCommand, self).__init__ ("regview savesnapshot",
      gdb.COMMAND_SUPPORT,
      gdb.COMPLETE_FILENAME)

  def invoke(self, arg, from_tty):
    rv.snapshot()
    with open(arg, "w") as text_file:
      text_file.write(pprint.pformat(rv.snap, indent=4))


class  RegviewLoadSnapshotCommand(gdb.Command):
  "Load a snapshot from a file."

  def __init__(self):
    super (RegviewLoadSnapshotCommand, self).__init__ ("regview loadsnapshot",
      gdb.COMMAND_SUPPORT,
      gdb.COMPLETE_FILENAME)

  def invoke(self, arg, from_tty):
    with open(arg, "r") as text_file:
      data=text_file.read()
      rv.snap = eval(data)


class  RegviewDiffsCommand(gdb.Command):
  "Diff of register state vs snapshot (from regivew snapshot)."

  def __init__(self):
    super (RegviewDiffsCommand, self).__init__ ("regview diffs",
      gdb.COMMAND_SUPPORT)

  def invoke(self, arg, from_tty):
    rv.diff_vs_snapshot()

class I2CScan(gdb.Command):
  "Scan an I2C bus for devices."
  def __init__(self):
    super (I2CScan, self).__init__ ("regview i2cscan",
      gdb.COMMAND_SUPPORT)

  def invoke(self, arg, from_tty):
    dbg = I2C.I2CDebugger(rv, arg)
    dbg.scan()

  def complete(self, arg, from_tty):
    i2c_registers = [ reg.get_fullname() for reg in rv.find_registers(arg) ]
    i2c_controllers = [ reg.split('_')[0] for reg in i2c_registers if reg.startswith("I2C") and "_" in reg ]
    return sorted(set(i2c_controllers))

class I2CRead(gdb.Command):
  "Read a register from an I2C device"
  def __init__(self):
    super (I2CRead, self).__init__ ("regview i2cread",
      gdb.COMMAND_SUPPORT)

  def invoke(self, arg, from_tty):
    argv = gdb.string_to_argv(arg)
    i2c_addr = int(argv[1], 0)
    reg_addr = int(argv[2], 0)
    if len(argv) > 3:
      reg_size = int(argv[3], 0)
    else:
      reg_size = 1

    dbg = I2C.I2CDebugger(rv, argv[0])
    print("I2C bus {}, device {:#04x}".format(argv[0], i2c_addr))

    for reg in range(reg_addr, reg_addr + reg_size):
      value = dbg.read(i2c_addr, reg)

      print("{:#04x}: {:#04x}".format(reg, value))

RegviewPrefixCommand()
RegviewLoadCommand()
RegviewLoadSvdCommand()
RegviewShowCommand()
RegviewSnapshotCommand()
RegviewDiffsCommand()
RegviewSaveSnapshotCommand()
RegviewLoadSnapshotCommand()
I2CScan()
I2CRead()

if __name__ == '__main__':
  print('Loaded', __file__)
  print('Type "regview <tab>" to see available commands.')
