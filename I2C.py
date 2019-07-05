# kate: space-indent on; indent-width 2; replace-tabs on


cr1_pe = 1 << 0
cr2_autoend = 1 << 25
cr2_start = 1 << 13
cr2_stop = 1 << 14
cr2_rd_wrn = 1  << 10
isr_nackf = 1 << 4
isr_stopf = 1 << 5
isr_rxne = 1 << 2
isr_txis = 1 << 1

class I2CNack(Exception):
  def __init__(self, s):
    self.msg = s
  def __str__(self):
    return self.msg

class I2CError(Exception):
  def __init__(self, s):
    self.msg = s
  def __str__(self):
    return self.msg

class I2CDebugger:
  def __init__(self, rv, controller):
    self.rv = rv
    self.controller = controller

    self.cr1 = self.find_register("CR1")
    self.cr2 = self.find_register("CR2")
    self.isr = self.find_register("ISR")
    self.icr = self.find_register("ICR")
    self.rxdr = self.find_register("RXDR")
    self.txdr = self.find_register("TXDR")

  def find_register(self, reg):
    regs = list(filter(lambda x: x.get_fullname() == self.controller + "_" + reg, self.rv.reg_defs))
    return regs[0]

  def scan(self):
    for address in range(0x08, 0x78):
      # Software reset
      cr1 = self.cr1.get_val()
      self.cr1.set_val(cr1 & ~cr1_pe)
      self.cr1.set_val(cr1 | cr1_pe)

      self.cr2.set_val(cr2_autoend | cr2_start | cr2_rd_wrn | (address << 1))

      isr = self.isr.get_val()
      if (isr & isr_nackf) == 0:
        print("Device {:#04x} found".format(address << 1))

      self.cr2.set_val(cr2_stop)

  def read(self, addr, reg):
    # ISR mask: Busy, Arbitration lost, Bus error, Stop, Nack
    isr_mask = 0x8330
    self.icr.set_val(isr_stopf)
    isr = self.isr.get_val()
    if isr & isr_mask != 0:
      raise I2CError("Unexpected ISR: {:#x}".format(isr))

    self.cr2.set_val(cr2_start | (addr & 0xfe) | (1 << 16))
    isr = self.isr.get_val() & isr_mask
    if isr & isr_nackf:
      self.icr.set_val(isr_nackf | isr_stopf)
      raise I2CNack("NACK when sending device address")
    if isr & isr_mask != 0x8000:
      raise I2CError("Unexpected ISR: {:#x}".format(isr))

    while self.isr.get_val() & isr_txis == 0:
      pass

    self.txdr.set_val(reg)
    isr = self.isr.get_val()
    if isr & isr_nackf:
      self.icr.set_val(isr_nackf | isr_stopf)
      raise I2CNack("NACK when sending register address")
    if isr & isr_mask != 0x8000:
      raise I2CError("Unexpected ISR: {:#x}".format(isr))

    self.cr2.set_val(cr2_start | cr2_autoend | cr2_rd_wrn | (addr & 0xfe) | (1 << 16))

    while True:
      isr = self.isr.get_val()
      if isr & isr_nackf:
        self.icr.set_val(isr_nackf | isr_stopf)
        raise I2CNack("NACK when receiving register value")

      if isr & isr_mask != 0x20:
        raise I2CError("Unexpected ISR: {:#x}".format(isr))

      if isr & isr_rxne:
        value = self.rxdr.get_val()
        self.icr.set_val(isr_stopf)
        return value
