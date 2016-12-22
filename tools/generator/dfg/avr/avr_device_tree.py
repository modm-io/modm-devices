# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import math
import logging

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

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
        p = {}

        did = AVRIdentifier.from_string(partname.lower())
        p['id'] = did

        LOGGER.info("Parsing '%s'", did.string)

        mcu = avr_mcu.getMcuForDevice(did)
        mcu = 'unsupported' if mcu == None else mcu
        p['mcu'] = mcu

        p['core'] = architecture.lower()

        p['define'] = '__AVR_' + partname + '__'

        # find the values for flash, ram and (optional) eeprom
        for memory_segment in device_file.query('//memory-segment'):
            name = memory_segment.get('name')
            size = int(memory_segment.get('size'), 16)
            if name in ['FLASH', 'APP_SECTION', 'PROGMEM']:
                p['flash'] = size
            elif name in ['IRAM', 'SRAM', 'INTERNAL_SRAM']:
                p['ram'] = size
            elif name == 'EEPROM':
                p['eeprom'] = size

        raw_modules = device_file.query("//peripherals/module/instance")
        modules = []
        signals = []
        gpios = []
        ports = []
        for m in raw_modules:
            tmp = {'module': m.getparent().get('name').lower(),
                   'instance': m.get('name').lower()}
            # module SPI has two instances USART0_SPI, USART1_SPI, wtf?
            if tmp['module'] == 'spi' and tmp['instance'].startswith("usart"): continue;
            if tmp['module'] == 'port':
                ports.append(tmp)
            else:
                modules.append(tmp)
        p['modules'] = sorted(list(set([(m['module'], m['instance']) for m in modules])))

        raw_signals = device_file.query("//peripherals/module/instance/signals/signal")
        modules_only = not len(raw_signals)
        p['modules_only'] = modules_only

        if modules_only:
            # Parse GPIOs manually from mask
            for port in ports:
                port = port['instance'][-1:]
                port_mask = device_file.query("//modules/module[@name='PORT']/register-group[@name='PORT{0}']/register[@name='PORT{0}']/@mask".format(port.upper()))
                if len(port_mask) == 0:
                    # The port mask is split up
                    port_mask = device_file.query("//modules/module[@name='PORT']/register-group[@name='PORT{0}']/register[@name='PORT{0}']/bitfield/@mask".format(port.upper()))
                    port_mask = sum([int(mask, 16) for mask in port_mask])
                else:
                    port_mask = int(port_mask[0], 16)
                for pos in range(8):
                    if (1 << pos) & port_mask:
                        gpios.append((port, str(pos)))
            gpios = sorted(gpios)
        else:
            for s in raw_signals:
                tmp = {'module': s.getparent().getparent().getparent().get('name').lower(),
                       'instance': s.getparent().getparent().get('name').lower()}
                tmp.update({k:v.lower() for k,v in s.items()})
                if tmp['group'] in ['p', 'pin'] or tmp['group'].startswith('port'):
                    gpios.append(tmp)
                else:
                    signals.append(tmp)
            gpios = sorted([(g['pad'][1], g['pad'][2]) for g in gpios])

        # Signal information is missing
        p['signals'] = signals
        p['gpios'] = gpios

        LOGGER.debug("Found GPIOs: [%s]", ", ".join([p.upper() + i for p,i in p['gpios']]))
        LOGGER.debug("Available Modules are:\n" + AVRDeviceTree._modulesToString(p['modules']))

        interrupts = []
        for i in device_file.query("//interrupts/interrupt"):
            interrupts.append({'position': i.get('index'), 'name': i.get('name')})
        p['interrupts'] = interrupts

        return p

    @staticmethod
    def _modulesToString(modules):
        string = ""
        mods = sorted(modules)
        char = mods[0][0][0:1]
        for module, instance in mods:
            if not instance.startswith(char):
                string += "\n"
            string += instance + " \t"
            char = instance[0][0:1]
        return string

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

        # AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-flash')
        # AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-ram')
        # AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-eeprom')
        AVRDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-mcu')

        def driverOrder(e):
            if e.name == 'driver':
                if e['name'] == 'core':
                    # place the core at the very beginning
                    return ('aaaaaaa', e['type'])
                if e['name'] == 'gpio':
                    # place the gpio at the very end
                    return ('zzzzzzz', e['type'])
                # sort remaining drivers by type and compatible strings
                return (e['name'], e['type'])
            return ("", "")
        tree.addSortKey(driverOrder)

        # Core
        core_child = tree.addChild('driver')
        core_child.setAttributes('name', 'core', 'type', p['core'])
        core_child.addSortKey(lambda e: (int(e['position']), e['name']) if e.name == 'vector' else (-1, ""))
        core_child.addSortKey(lambda e: (e['name'], int(e['size'])) if e.name == 'memory' else ("", -1))
        for memory in ['flash', 'ram', 'eeprom']:
            if memory not in p: continue;
            memory_section = core_child.addChild('memory')
            memory_section.setAttribute('name', memory)
            memory_section.setAttribute('size', p[memory])
        # for vector in p['interrupts']:
        #     vector_section = core_child.addChild('vector')
        #     vector_section.setAttributes(['position', 'name'], vector)

        # Clock
        clock_child = tree.addChild('driver')
        clock_child.setAttributes('name', 'clock', 'type', 'avr')

        modules = {}
        for m, i in p['modules']:
            # filter out non-peripherals
            if m in ['cpu', 'jtag', 'exint', 'fuse', 'gpio']: continue;
            if m in ['lockbit', 'boot_load']: continue;
            # ATtiny AVR8X has more peripherals
            if m in ['clkctrl', 'cpuint']: continue;
            if m not in modules:
                modules[m] = [i]
            else:
                modules[m].append(i)

        # add all other modules
        for name, instances in modules.items():
            driver = tree.addChild('driver')
            dtype = name
            compatible = 'avr'

            if name.startswith('tc'):
                dtype = 'tc'
                compatible = name

            driver.setAttributes('name', dtype, 'type', compatible)
            # Add all instances to this driver
            if any(i != dtype for i in instances):
                driver.addSortKey(lambda e: e['value'])
                for i in instances:
                    inst = driver.addChild('instance')
                    inst.setValue(i[len(dtype):])

        # GPIO driver
        gpio_driver = tree.addChild('driver')
        gpio_driver.setAttributes('name', 'gpio', 'type', 'avr')
        gpio_driver.addSortKey(lambda e : (e['port'], int(e['pin'])))
        for port, pin in p['gpios']:
            pin_driver = gpio_driver.addChild('gpio')
            pin_driver.setAttributes('port', port.upper(), 'pin', pin)
            pin_driver.addSortKey(lambda e: (e['driver'],
                                             e['instance'] if e['instance'] is not None else '',
                                             e['name'] if e['name'] is not None else ''))
            # add all signals
            for s in [s for s in p['signals'] if s['pad'] == ("p" + port + pin)]:
                driver, instance, name = s['module'], s['instance'], s['group']
                if driver.startswith('tc'): driver = 'tc';
                if driver == 'cpu': driver = 'core'; instance = 'core';
                # add the af node
                pin_signal = {'driver': driver}
                if instance != driver:
                    pin_signal['instance'] = instance.replace(driver, '')
                if name != driver and name != 'int':
                    if 'index' in s: name += s['index'];
                    pin_signal['name'] = name
                elif 'index' in s:
                    pin_signal['name'] = s['index']
                if "name" not in pin_signal:
                    LOGGER.error("%s has no name!", s)
                    continue
                af = pin_driver.addChild('signal')
                af.setAttributes(['driver', 'instance', 'name'], pin_signal)

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
    def from_file(filename):
        p = AVRDeviceTree._properties_from_file(filename)
        if p is None: return None;
        return AVRDeviceTree._device_tree_from_properties(p)
