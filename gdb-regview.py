import gdb
import struct
import sys
import os
import pdb
import pprint

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
      print "Unknown register %s" % arg
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


RegviewPrefixCommand()
RegviewLoadCommand()
RegviewShowCommand()
RegviewSnapshotCommand()
RegviewDiffsCommand()
RegviewSaveSnapshotCommand()
RegviewLoadSnapshotCommand()

if __name__ == '__main__':
  print 'Loaded', __file__
  print 'Type "regview <tab>" to see available commands.'
