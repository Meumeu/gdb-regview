gdb-regview
===========

This gdb plugin makes viewing MCU register contents from gdb easier and more convenient. Originally targeted at STM32 microcontrollers. Uses xml register definition files. May require appropriate debugger probe support for the intended target.

### Usage

From gdb, first load the plugin, then load the desired definitions xml, and finally show register contents:

`(gdb) source /path/to/gdb-regview.py`

`(gdb) regview load /path/to/definitions.xml`

`(gdb) regview show REGISTER_NAME`

`(gdb) regview show REGISTER_NAME_WITH_GLOB`

For example:

```
regview show ADC?_CR1
regview show DMA1_Channel*CCR*
```

Tab completion is enabled for register names. One may wish to automatically load the plugin and register definitions using a `.gdbinit` file.


### Snapshot

To capture a snapshot within the current session

`(gdb) regview snapshot`

Later you can diff:

`(gdb) regview diffs`

which will give something list this:

```
ADC1_DR:DATA  0xe95->0xff7
DMA1_Channel1_CNDTR1:NDT  0xc2->0xcc
DMA1_Channel2_CNDTR2:NDT  0x41->0x3a
DMA1_Channel3_CNDTR3:NDT  0x63->0x46
GPIOA_IDR:IDR9  0x0->0x1
TIM1_CCR1:CCR1  0x270->0x39a
```

You can also save the snapshot to a file:

`(gdb) regview savesnapshot snap_test.txt`

And load it later:

`(gdb) regview loadsnapshot snap_test.txt`

`(gdb) regview diffs`


### Register Definitions

Register definitions use the format defined by the Eclipse Embedded Systems Register View [(http://sourceforge.net/projects/embsysregview/)](http://sourceforge.net/projects/embsysregview/). In fact, it is recommended to use the register definition xml files included in this project.

A sample of STM32 register definitions are included in the `./defs` directory. The complete collection is available here: [http://sourceforge.net/p/embsysregview/code/HEAD/tree/trunk/org.eclipse.cdt.embsysregview.data/data/](http://sourceforge.net/p/embsysregview/code/HEAD/tree/trunk/org.eclipse.cdt.embsysregview.data/data/)

### Register Name Modification

In order to make accessing registers for groups of peripherals, the register name is modified compared to how it is available in the embsysregview xml files. Rather than `periph_registername`, the registers are referenced as `registergroup_registername`.

For example, on an STM32, there are several ADCs: `ADC1`, `ADC2`, etc. Each ADC has an `ADC_CR` register, which will be referenced as `ADC1_CR` (which is closer to the representation in the datasheet/reference manual).
