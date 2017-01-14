# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import math
import logging

from ..device_tree import DeviceTree
from ..input.xml import XMLReader
from ..peripheral import Peripheral
from ..register import Register

from .avr_identifier import AVRIdentifier
from . import avr_io
from . import avr_mcu

LOGGER = logging.getLogger('dfg.avr.reader')

class AVRDeviceTree:
    """ AVRDeviceTree
    This AVR specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """

    @staticmethod
    def _properties_from_file(filename):
        device_file = XMLReader(filename)

        device = device_file.query("//device")[0]
        partname = device.get('name')
        architecture = device.get('architecture')
        properties = {}

        did = AVRIdentifier.from_string(partname.lower())
        properties['id'] = did

        LOGGER.info("Parsing '%s'", did.string)

        mcu = avr_mcu.getMcuForDevice(did)
        mcu = 'unsupported' if mcu == None else mcu
        properties['mcu'] = mcu

        properties['core'] = architecture.lower()
        if (architecture not in ['AVR8', 'AVR8L', 'AVR8_XMEGA']):
            LOGGER.error("Sorry, only ATtiny, ATmega, ATxmega and AT90 targets can be parsed corretly.")
            exit(1)

        properties['define'] = '__AVR_' + partname + '__'

        # find the values for flash, ram and (optional) eeprom
        for memory_segment in device_file.query('//memory-segment'):
            name = memory_segment.get('name')
            size = int(memory_segment.get('size'), 16)
            if name in ['FLASH', 'APP_SECTION']:
                properties['flash'] = size
            elif name in ['IRAM', 'SRAM', 'INTERNAL_SRAM']:
                properties['ram'] = size
            elif name == 'EEPROM':
                properties['eeprom'] = size

        gpios = []
        properties['gpios'] = gpios
        peripherals = []
        properties['peripherals'] = peripherals
        omodules = device_file.compactQuery("//peripherals/module/instance/@name")
        modules = []
        properties['modules'] = modules

        LOGGER.debug("Available Modules are:\n" + AVRDeviceTree._modulesToString(omodules))

        if did["family"] == 'xmega':
            for dev in [d for d in avr_io.xmega_pins if d['type'] == did["type"]]:
                for port in dev['gpio']:
                    port_dict = AVRDeviceTree._getAttributedPortDictionary(port)
                    gpios.extend(port_dict)

            for mod in device_file.query("//peripherals/module/instance"):
                name = mod.get('name')

                if any(name.startswith(per) for per in ["TWI", "USART", "SPI", "ADC", "USB", "DAC", "TC"]):
                    if not name.endswith("SPI"):
                        modules.append(name)
                        continue

            for peripheral in modules:
                base = None
                for per in ["TWI", "USART", "SPI", "ADC", "USB", "DAC", "TC"]:
                    if peripheral.startswith(per):
                        base = per
                        break
                if base:
                    port = peripheral.replace(base, "")
                    base = base.lower()
                    instance = None
                    if len(port) == 2:
                        instance = port[1:]
                        port = port[:1]
                    if base in avr_io.xmega_peripheral_pins:
                        module = list(avr_io.xmega_peripheral_pins[base])
                        for pin in [p for p in module if instance == None or instance == p["instance"]]:
                            for gpio in [g for g in gpios if g['port'] == port and g['id'] == pin['id']]:
                                if base == 'twi':
                                    af = {'peripheral' : 'I2cMaster' + port,
                                          'name': pin['name'].capitalize(),
                                          'type': pin['dir']}
                                    gpio['af'].append(af)
                                elif base == 'spi':
                                    af = {'peripheral' : 'SpiMaster' + port,
                                          'name': pin['name'].capitalize(),
                                          'type': pin['dir']}
                                    if 'remap' in pin:
                                        af.update({'remap': pin['remap']})
                                    gpio['af'].append(af)
                                    negate = {'in': 'out', 'out': 'in', 'io': 'io'}
                                    repl = {'mosi': 'simo', 'miso': 'somi', 'sck': 'sck', 'ss': 'ss'}
                                    af2 = {'peripheral' : 'SpiSlave' + port,
                                          'name': repl[pin['name']].capitalize(),
                                          'type': negate[pin['dir']]}
                                    if 'remap' in pin:
                                        af2.update({'remap': pin['remap']})
                                    gpio['af'].append(af2)
                                elif base == 'usart':
                                    af = {'peripheral' : 'Uart' + port + instance,
                                          'name': pin['name'].capitalize(),
                                          'type': pin['dir']}
                                    if 'remap' in pin:
                                        af.update({'remap': pin['remap']})
                                    gpio['af'].append(af)
                                    repl = {'txd': 'mosi', 'rxd': 'miso', 'xck': 'sck'}
                                    af = {'peripheral' : 'UartSpiMaster' + port + instance,
                                          'name': repl[pin['name']].capitalize(),
                                          'type': pin['dir']}
                                    if 'remap' in pin:
                                        af.update({'remap': pin['remap']})
                                    gpio['af'].append(af)
                                elif base == 'tc':
                                    af = {'peripheral' : 'TimerCounter' + port + instance,
                                          'name': pin['name'].capitalize(),
                                          'type': pin['dir']}
                                    if 'remap' in pin:
                                        af.update({'remap': pin['remap']})
                                    gpio['af'].append(af)

        else:
            for mod in device_file.query("//modules/module"):
                name = mod.get('name')

                if "PORT" in name:
                    module = AVRDeviceTree.createModule(device_file, omodules, name)
                    gpios.extend(AVRDeviceTree._gpioFromModule(module))

                if any(name.startswith(per) for per in ["EXTERNAL_INT", "TWI", "USART", "SPI", "AD_CON", "USB", "CAN", "DA_CON", "TIMER", "PORT"]):
                    modules.append(name)
                    module = AVRDeviceTree.createModule(device_file, omodules, name)
                    peripherals.append(module)
                    continue

            for pin_array in [a for a in avr_io.pins if did.string in a['devices']]:
                for name in ['pcint', 'extint']:
                    if name in pin_array:
                        for module in pin_array[name]:
                            for gpio in [g for g in gpios if g['port'] == module['port'] and g['id'] == module['id']]:
                                gpio[name] = module['int']

                for name in ['spi', 'i2c']:
                    if name in pin_array:
                        for module in pin_array[name]:
                            for gpio in [g for g in gpios if g['port'] == module['port'] and g['id'] == module['id']]:
                                if name == 'i2c':
                                    af = {'peripheral' : 'I2cMaster',
                                          'name': module['name'].capitalize(),
                                          'type': module['dir']}
                                    gpio['af'].append(af)
                                elif name == 'spi':
                                    af = {'peripheral' : 'SpiMaster',
                                          'name': module['name'].capitalize(),
                                          'type': module['dir']}
                                    gpio['af'].append(af)
                                    negate = {'in': 'out', 'out': 'in', 'io': 'io'}
                                    repl = {'mosi': 'simo', 'miso': 'somi', 'sck': 'sck', 'ss': 'ss'}
                                    af2 = {'peripheral' : 'SpiSlave',
                                          'name': repl[module['name']].capitalize(),
                                          'type': negate[module['dir']]}
                                    gpio['af'].append(af2)
                                # elif name == 'usi':
                                #   af = {'peripheral' : 'Usi',
                                #         'name': module['name'].capitalize(),
                                #         'type': module['dir']}
                                #   gpio['af'].append(af)

                for name in ['uart0', 'uart1', 'uart2', 'uart3']:
                    if name in pin_array:
                        for module in pin_array[name]:
                            for gpio in [g for g in gpios if g['port'] == module['port'] and g['id'] == module['id']]:
                                af = {'peripheral' : name.capitalize(),
                                      'name': module['name'].capitalize(),
                                      'type': module['dir']}
                                gpio['af'].append(af)
                                if 'uartspi' in pin_array:
                                    repl = {'txd': 'mosi', 'rxd': 'miso', 'xck': 'sck'}
                                    af = {'peripheral' : 'UartSpiMaster' + name[4:],
                                          'name': repl[module['name']].capitalize(),
                                          'type': module['dir']}
                                    gpio['af'].append(af)

        return properties

    @staticmethod
    def createModule(device_file, modules, name):
        if name in modules:
            return Peripheral(name, AVRDeviceTree._registersOfModule(device_file, name))
        else:
            LOGGER.error("'" + name + "' not a module!")
            LOGGER.error("Available modules are:\n" + AVRDeviceTree._modulesToString(modules))
            return None

    @staticmethod
    def _registersOfModule(device_file, module):
        results = device_file.query("//register-group[@name='" + module + "']/register")
        registers = []
        for res in results:
            registers.append(AVRDeviceTree._translateRegister(res))
        return registers

    @staticmethod
    def _translateRegister(queryResult):
        mask = queryResult.get('mask')
        size = int(queryResult.get('size'))
        name = queryResult.get('name')
        register = Register(name)
        register.size = size

        if mask == None:
            fields = queryResult.findall('bitfield')
            for field in fields:
                fname = field.get('name')
                if 'Res' in fname:
                    continue

                fmask = int(field.get('mask'), 16)
                flsb = field.get('lsb')
                flsb = int(flsb) if flsb is not None else 0

                if bin(fmask).count("1") > 1:
                    start = flsb
                    for iii in range(8 * size):
                        if fmask & 2 ** (iii):
                            name = fname + str(start)
                            start += 1
                            register.addField(name, iii)
                else:
                    register.addField(fname, int(math.log(fmask, 2)))
        else:
            fmask = int(mask, 16)
            flsb = queryResult.get('lsb')
            flsb = int(flsb) if flsb is not None else 0

            if bin(fmask).count("1") > 1:
                start = flsb
                for iii in range(8 * size):
                    if fmask & 2 ** (iii):
                        register.addField('data' + str(start), iii)
                        start += 1

        return register

    @staticmethod
    def _modulesToString(modules):
        string = ""
        char = modules[0][0:1]
        for module in modules:
            if not module.startswith(char):
                string += "\n"
            string += module + " \t"
            char = module[0][0:1]
        return string

    @staticmethod
    def _gpioFromModule(module):
        """
        This tries to get information about available pins in a port and
        returns a dictionary containing the port name and available pins
        as a bit mask.
        """
        port = module.name[4:5]
        for reg in module.registers:
            if module.name == reg.name:
                mask = reg.maskFromRegister()
                return AVRDeviceTree._getAttributedPortDictionary({'port': port, 'mask': mask})
        return None

    @staticmethod
    def _getAttributedPortDictionary(port):
        ports = []
        mask = port['mask']
        pin_id = 0

        while pin_id < 16:
            if mask & 0x01:
                ports.append({'port': port['port'], 'id': str(pin_id), 'af': []})
            mask >>= 1
            pin_id += 1

        return ports


    @staticmethod
    def _device_tree_from_properties(p):
        tree = DeviceTree('device')
        tree.ids.append(p['id'])
        LOGGER.info(("Generating Device Tree for '%s'" % p['id'].string))

        def topLevelOrder(e):
            order = ['attribute-flash', 'attribute-ram', 'attribute-eeprom', 'attribute-core', 'attribute-mcu', 'header', 'attribute-define']
            if e.name in order:
                if e.name in ['attribute-flash', 'attribute-eeprom', 'attribute-ram']:
                    return (order.index(e.name), int(e['value']))
                else:
                    return (order.index(e.name), e['value'])
            return (len(order), -1)
        tree.addSortKey(topLevelOrder)

        # search the io dictionary for this device
        # we only need one pin name to identify the device group
        io = [a for a in avr_io.pins if p['id'].string in a['devices']]
        if len(io) > 0:
            io = io[0]
        else:
            io = {}
            if p['id']["family"] != 'xmega':
                LOGGER.warning("IO not found for device '%s' with pin-name: '%s'", p['id'].string, pin_name)
        p['io'] = io

        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-flash')
        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-ram')
        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-eeprom')
        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-core')
        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-mcu')

        def driverOrder(e):
            if e.name == 'driver':
                if e['type'] == 'core':
                    # place the core at the very beginning
                    return ('aaaaaaa', e['compatible'])
                if e['type'] == 'gpio':
                    # place the gpio at the very end
                    return ('zzzzzzz', e['compatible'])
                # sort remaining drivers by type and compatible strings
                return (e['type'], e['compatible'])
            return ("", "")
        tree.addSortKey(driverOrder)

        core_child = tree.addChild('driver')
        core_child.setAttributes('type', 'core', 'compatible', 'avr')
        core_child.setIdentifier(lambda e: e['type'] + e['compatible'])

        # ADC
        AVRDeviceTree.addAdcToNode(p, tree)
        # Clock
        clock_child = tree.addChild('driver')
        clock_child.setAttributes('type', 'clock', 'compatible', 'avr')
        clock_child.setIdentifier(lambda e: e['type'] + e['compatible'])
        # DAC
        AVRDeviceTree.addDacToNode(p, tree)
        # I2C aka TWI
        AVRDeviceTree.addI2cToNode(p, tree)
        # SPI
        AVRDeviceTree.addSpiToNode(p, tree)
        # Timer
        AVRDeviceTree.addTimerToNode(p, tree)
        # UART
        AVRDeviceTree.addUartToNode(p, tree)
        # USI can be used to emulate UART, SPI and I2C, so there should not be a seperate driver for it.
        # AVRDeviceTree.addUsiToNode(p, tree)
        # GPIO
        AVRDeviceTree.addGpioToNode(p, tree)

        return tree

    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split('-')[-1]
        if pname not in p: return;
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setValue(prop)
            child.setIdentifier(lambda e: e.name)

    @staticmethod
    def _compatible_family(p, family):
        if family == None:
            if p['id']["family"] in ['xmega', '90']:
                return p['id']["family"]
            return 'avr'
        return family

    @staticmethod
    def addModuleAttributesToNode(p, node, peripheral, name, family=None):
        family = AVRDeviceTree._compatible_family(p, family)

        if any(m for m in p['modules'] if m.startswith(peripheral)):
            driver = node.addChild('driver')
            driver.setAttributes('type', name, 'compatible', family)
            driver.setIdentifier(lambda e: e['type'] + e['compatible'])

    @staticmethod
    def addModuleInstancesAttributesToNode(p, node, peripheral, name, family=None):
        family = AVRDeviceTree._compatible_family(p, family)

        driver = node.addChild('driver')
        driver.setAttributes('type', name, 'compatible', family)
        driver.addSortKey((lambda e: e['value']) if p['id']["family"] == 'xmega' else (lambda e: int(e['value'])))
        driver.setIdentifier(lambda e: e['type'] + e['compatible'])

        instances = []
        for module in [m for m in p['modules'] if m.startswith(peripheral)]:
            instances.append(module[len(peripheral):])

        for instance in reversed(instances):
            child = driver.addChild('instance')
            child.setValue(instance)
            child.setIdentifier(lambda e: e.name)

    @staticmethod
    def addI2cToNode(p, node):
        if p['id']["family"] == 'xmega':
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'TWI', 'i2c')
        else:
            AVRDeviceTree.addModuleAttributesToNode(p, node, 'TWI', 'i2c', 'avr')

    @staticmethod
    def addSpiToNode(p, node):
        if p['id']["family"] == 'xmega':
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'SPI', 'spi')
        else:
            AVRDeviceTree.addModuleAttributesToNode(p, node, 'SPI', 'spi', 'avr')

    @staticmethod
    def addAdcToNode(p, node):
        if p['id']["family"] == 'xmega':
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'ADC', 'adc')
        else:
            AVRDeviceTree.addModuleAttributesToNode(p, node, 'AD_CONVERTER', 'adc')

    @staticmethod
    def addDacToNode(p, node):
        if p['id']["family"] == 'xmega':
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'DAC', 'dac')
        else:
            AVRDeviceTree.addModuleAttributesToNode(p, node, 'DA_CONVERTER', 'dac')

    @staticmethod
    def addUsiToNode(p, node):
        if p['id']["family"] != 'xmega':
            AVRDeviceTree.addModuleAttributesToNode(p, node, 'USI', 'usi')

    @staticmethod
    def addTimerToNode(p, node):
        if p['id']["family"] == 'xmega':
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'TC', 'timer')
        else:
            AVRDeviceTree.addModuleInstancesAttributesToNode(p, node, 'TIMER_COUNTER_', 'timer', p['id']["family"])

    @staticmethod
    def addUartToNode(p, node):
        # this is special, some AT90_Tiny_Megas can put their USART into SPI mode
        # we have to parse this specially.
        uartSpi = 'uartspi' in p['io'] or p['id']["family"] == 'xmega'

        instances = []
        for module in [m for m in p['modules'] if m.startswith('USART')]:
            if p['id']["family"] == 'xmega':
                instances.append(module[5:7])
            else:
                # some device only have a 'USART', but we want 'USART0'
                instances.append((module + '0')[5:6])
        instances = list(set(instances))

        driver = node.addChild('driver')
        driver.setAttributes('type', 'uart', 'compatible', 'xmega' if p['id']["family"] == 'xmega' else 'avr')
        driver.addSortKey((lambda e: e['value']) if p['id']["family"] == 'xmega' else (lambda e: int(e['value'])))
        driver.setIdentifier(lambda e: e['type'] + e['compatible'])
        if uartSpi:
            spi_driver = node.addChild('driver')
            spi_driver.setAttributes('type', 'spi', 'compatible', ('xmega' if p['id']["family"] == 'xmega' else 'avr') + "_uart")
            spi_driver.addSortKey((lambda e: e['value']) if p['id']["family"] == 'xmega' else (lambda e: int(e['value'])))
            spi_driver.setIdentifier(lambda e: e['type'] + e['compatible'])

        for instance in instances:
            child = driver.addChild('instance')
            child.setValue(instance)
            child.setIdentifier(lambda e: e.name)

            if uartSpi:
                child = spi_driver.addChild('instance')
                child.setValue(instance)
                child.setIdentifier(lambda e: e.name)

    @staticmethod
    def addGpioToNode(p, node):
        props = p['gpios']

        driver = node.addChild('driver')
        driver.setAttributes('type', 'gpio', 'compatible', 'xmega' if p['id']["family"] == 'xmega' else 'avr')
        driver.setIdentifier(lambda e: e['type'] + e['compatible'])
        driver.addSortKey(lambda e : (e['port'], int(e['id'])))

        for gpio in props:
            gpio_child = driver.addChild('gpio')
            gpio_child.addSortKey(lambda e : (e['peripheral'], e['name']))
            gpio_child.setAttributes(['port', 'id', 'pcint', 'extint'], gpio)
            for af in gpio['af']:
                af_child = gpio_child.addChild('af')
                af_child.setAttributes(['peripheral', 'name', 'type'], af)

    @staticmethod
    def from_file(filename):
        p = AVRDeviceTree._properties_from_file(filename)
        return AVRDeviceTree._device_tree_from_properties(p)
