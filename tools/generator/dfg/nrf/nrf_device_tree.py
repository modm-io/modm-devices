# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# Copyright (c)      2020, Hannes Ellinger
# All rights reserved.

import math
import logging
import re
import os

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .nrf_identifier import NRFIdentifier

LOGGER = logging.getLogger('dfg.nrf.reader')

class NRFDeviceTree:
    """ NRFDeviceTree
    This NRF specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """

    @staticmethod
    def _properties_from_file(ld_filename):
        xml_filename = re.sub(r'\_\w{4}.ld', '.svd', ld_filename)
        device_file = XMLReader(xml_filename)
        p = {}

        partname = ld_filename.split('/')[-1]
        partname = partname.split('.')[0]
        partname = partname.replace('_', '-')

        did = NRFIdentifier.from_string(partname.lower())
        p['id'] = did

        LOGGER.info("Parsing '%s'", did.string)

        # information about the core and architecture
        core = device_file.query("//device/cpu/name")[0].text.lower().replace("cm", "cortex-m")
        if device_file.query("//device/cpu/fpuPresent")[0].text == '1':
            core += "f"
        p["core"] = core


        # find the values for flash and ram
        memlines = []
        with open(ld_filename, 'r') as linkerfile:
            status = 0
            for line in linkerfile:
                if status == 0 and "MEMORY" in line:
                    status = 1
                elif status == 1 and "{" in line:
                    status = 2
                elif status == 2:
                    if "}" in line:
                        status = 3
                    else:
                        memlines.append(line)

        memories = []

        for memline in memlines:
            matchString = r"  (?P<name>\w*) \((?P<access>\w*)\) : ORIGIN = (?P<start>0x\d*), LENGTH = (?P<size>0x\d*)"
            match = re.search(matchString, memline)
            memories.append({
                "name": match.group("name").lower(),
                "access": match.group("access").lower(),
                "size": str(int(match.group("size").lower(), 16)),
                "start": match.group("start").lower()})

        p["memories"] = memories


        # Signals
        signals = {}
        raw_signals = device_file.query("//peripherals/peripheral/registers/cluster")
        for s in raw_signals:
            if s.find('name').text == "PSEL":

                # find parent peripheral
                parent_peripheral_instance = s.getparent().getparent().find('name').text.lower()
                signals[parent_peripheral_instance] = []

                # find all signals of peripheral
                signal_elements = s.findall('register/name')
                for signal_element in signal_elements:
                    signal_name = signal_element.text.lower()
                    signals[parent_peripheral_instance].append(signal_name)


        # drivers and gpios
        raw_modules = device_file.query("//peripherals/peripheral")
        modules = []
        ports = {}
        gpios = []
        for m in raw_modules:
            modulename = m.find('name').text
            moduledesc = m.find('description').text

            if "GPIO Port" in moduledesc:
                # omit the leading P of the port names, also of the derived ports
                portnumber = modulename[1:]
                if m.get('derivedFrom') is not None:
                    portsize = ports[m.get('derivedFrom')[1:]]
                else:
                    portsize = int(m.find('size').text, base=0)

                ports[portnumber] = portsize
                for i in range(portsize):
                    gpios.append((portnumber, str(i)))

            else:
                matchString = r"(?P<module>.*\D)(?P<instance>\d*$)"
                match = re.search(matchString, modulename)
                modules.append({'module': match.group("module").lower(), 'instance': modulename.lower()})

                # copy available signals to all derived peripherals
                if m.get('derivedFrom') is not None:
                    if m.get('derivedFrom').lower() in signals:
                        LOGGER.debug(modulename.lower() + " is derived from " + m.get('derivedFrom').lower())
                        signals[modulename.lower()] = signals[m.get('derivedFrom').lower()]
        p['modules'] = sorted(list(set([(m['module'], m['instance']) for m in modules])))
        p['gpios'] = gpios
        p['signals'] = []
        for instance in signals:
            for signal in signals[instance]:
                matchString = r"(?P<module>.*\D)(?P<instance>\d*$)"
                match = re.search(matchString, instance)
                if not "[%s]" in signal:  # TODO take care of multichannel signals like OUT[%s] of PWM peripheral
                    p['signals'].append({'driver': match.group("module").lower(), 'instance': instance, 'name': signal})


        interrupts = []
        raw_interrupt = device_file.query("//peripherals/peripheral/interrupt")
        for i in raw_interrupt:
            interruptname = i.find('name').text
            interruptnum = i.find('value').text
            interrupts.append({'position': interruptnum, 'name': interruptname})

        # Unique interrupts
        p['interrupts'] = []
        for interrupt in interrupts:
            if interrupt not in p['interrupts']:
                p['interrupts'].append(interrupt)

        LOGGER.debug("Found GPIOs: [%s]", ", ".join([p.upper() + "." + i for p,i in p['gpios']]))
        LOGGER.debug("Available Modules are:\n" + NRFDeviceTree._modulesToString(p['modules']))
        LOGGER.debug("Found Signals:")
        for sig in p['signals']:
            LOGGER.debug("    %s", sig)
        LOGGER.debug("Found Interrupts:")
        for intr in p['interrupts']:
            LOGGER.debug("    %s", intr)

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

        def topLevelOrder(e):
            order = ['attribute-flash', 'attribute-ram', 'attribute-eeprom', 'attribute-core', 'attribute-mcu', 'header', 'attribute-define']
            if e.name in order:
                if e.name in ['attribute-flash', 'attribute-eeprom', 'attribute-ram']:
                    return (order.index(e.name), int(e['value']))
                else:
                    return (order.index(e.name), e['value'])
            return (len(order), -1)
        # tree.addSortKey(topLevelOrder)

        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-flash')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-ram')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-eeprom')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-mcu')

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

        for section in p["memories"]:
            memory_section = core_child.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
        # sort the node children by start address and size
        core_child.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))

        # for memory in ['flash', 'ram', 'lpram', 'eeprom']:
        #     if memory not in p: continue;
        #     memory_section = core_child.addChild('memory')
        #     memory_section.setAttribute('name', memory)
        #     memory_section.setAttribute('size', p[memory])

        for vector in p['interrupts']:
            if int(vector['position']) < 0: continue;
            vector_section = core_child.addChild('vector')
            vector_section.setAttributes(['position', 'name'], vector)

        modules = {}
        for m, i in p['modules']:
            # filter out non-peripherals: fuses, micro-trace buffer
            if m in ['fuses', 'mtb', 'systemcontrol', 'systick', 'hmatrixb', 'hmatrix']: continue;
            if m not in modules:
                modules[m] = [i]
            else:
                modules[m].append(i)


        compatible = p['id']['platform'] + p['id']['family']
        # add all other modules
        for name, instances in modules.items():
            driver = tree.addChild('driver')
            dtype = name

            driver.setAttributes('name', dtype, 'type', compatible)
            # Add all instances to this driver
            if any(i != dtype for i in instances):
                driver.addSortKey(lambda e: e['value'])
                for i in instances:
                    inst = driver.addChild('instance')
                    inst.setValue(i[len(dtype):])

        # GPIO driver
        gpio_driver = tree.addChild('driver')
        gpio_driver.setAttributes('name', 'gpio', 'type', compatible)
        # gpio_driver.addSortKey(lambda e : (e['port'], int(e['pin'])))

        # add all signals
        for s in p['signals']:
            driver, instance, name = s['driver'], s['instance'], s['name']
            # add the af node
            gpio_signal = {'driver': driver}
            if instance != driver:
                gpio_signal['instance'] = instance.replace(driver, '')
            if name != driver and name != 'int':
                if 'index' in s: name += s['index'];
                gpio_signal['name'] = name
            elif 'index' in s:
                gpio_signal['name'] = s['index']
            if "name" not in gpio_signal:
                LOGGER.error("%s has no name!", s)
                continue

            af = gpio_driver.addChild('signal')
            af.setAttributes(['driver', 'instance', 'name'], gpio_signal)

        # add all GPIOs
        for port, pin in p['gpios']:
            pin_driver = gpio_driver.addChild('gpio')
            pin_driver.setAttributes('port', port, 'pin', pin)
            pin_driver.addSortKey(lambda e: (e['driver'],
                                             e['instance'] if e['instance'] is not None else '',
                                             e['name'] if e['name'] is not None else ''))

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

    @staticmethod
    def from_file(filename):
        p = NRFDeviceTree._properties_from_file(str(filename))
        if p is None: return None;
        return NRFDeviceTree._device_tree_from_properties(p)
