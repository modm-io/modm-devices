# -*- coding: utf-8 -*-
# Copyright (c) 2022, Andrey Kunitsyn
# All rights reserved.

import math
import logging
import re
import os

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .rp_identifier import RPIdentifier

LOGGER = logging.getLogger('dfg.rp.reader')


class RPDeviceTree:
    """ RPDeviceTree
    This RP specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """
    @staticmethod
    def func_to_signal(modules,func):
        parts = func['name'].split('_')
        idx = 0
        name = parts[idx]
        while (not name in modules):
            idx = idx + 1
            if idx >= len(parts):
                raise Exception("Not found module for func {}".format(func))
            name = name + '_' + parts[idx]
        m = modules[name]
        eidx = len(parts)-1
        digits = r"^(\d)+$"
        #print('process {} {}/{}'.format(func,idx,eidx))
        while re.match(digits,parts[eidx]) and eidx>idx:
            #print('skip {}'.format(parts[eidx]))
            eidx = eidx - 1
        res = {
            'driver': m['module'],
            'name': '_'.join(parts[idx+1:eidx+1]),
            'af': func['value'],
        }
        if res['name'] == '':
            res['name'] = 'pad' #default name
        if m['module'] != m['instance']:
            res['instance']=m['instance'][len(m['module']):]
        return res

    @staticmethod
    def make_clk_src_name(name):
        if name.startswith('clksrc_'):
            return name[7:]
        if name.startswith('clk_'):
            return name[4:]
        if name.endswith('_clksrc'):
            return name[0:-7]
        if name.endswith('_clksrc_ph'):
            return name[0:-10]
        return name

    @staticmethod
    def _properties_from_file(svd_filename):
        device_file = XMLReader(svd_filename)
        p = {}

        partname = svd_filename.split('/')[-1]
        partname = partname.split('.')[0]

        did = RPIdentifier.from_string(partname.lower())
        p['id'] = did

        LOGGER.info("Parsing '%s'", did.string)

        # information about the core and architecture
        core = device_file.query("//device/cpu/name")[0].text.lower().replace("cm", "cortex-m").replace("plus", "+")
        if device_file.query("//device/cpu/fpuPresent")[0].text == '1':
            core += "f"
        p["core"] = core

        # @todo
        memories = [
            # RAM(rwx) : ORIGIN =  0x20000000, LENGTH = 256k
            # CORE1(rwx) : ORIGIN = 0x20040000, LENGTH = 4k
            # CORE0(rwx) : ORIGIN = 0x20041000, LENGTH = 4k
            {
                "name": "ram",
                "access": "rwx",
                "size": str(int("0x40000",16)),
                "start": "0x20000000"
            },
            {
                "name": "core1",
                "access": "rwx",
                "size": str(int("0x1000",16)),
                "start": "0x20040000"
            },
            {
                "name": "core0",
                "access": "rwx",
                "size": str(int("0x1000",16)),
                "start": "0x20041000"
            },
        ]

        p["memories"] = memories



        # drivers and gpios
        raw_modules = device_file.query("//peripherals/peripheral")
        modules = []
        gpios = []
        dma_channels = []
        modules_map = {}
        clocks = []

        modules.append({'module':'jtag','instance':'jtag'})
        modules.append({'module':'usb','instance':'usb'})
        modules.append({'module':'xip','instance':'xip'})

        for m in raw_modules:
            modulename = m.find('name').text
            if modulename == 'IO_BANK0':
                gpionameMatchString = r"^GPIO(?P<name>.*)_STATUS$"
                for r in m.findall('./registers/register'):
                    if r.find('description') is not None and r.find('description').text == 'GPIO status':
                        match = re.search(gpionameMatchString,r.find('name').text)
                        name = match.group('name').lower()
                        ctrl = m.find("./registers/register[name='GPIO"+name+"_CTRL']")
                        func = ctrl.find("./fields/field[name='FUNCSEL']")
                        funcs = [];
                        for f in func.findall('./enumeratedValues/enumeratedValue'):
                            if f.find('name').text != 'null':
                                funcs.append({'name':f.find('name').text,'value':f.find('value').text})
                        pin = {
                            'name':name,
                            'bank':'bank0',
                            'idx': int(name),
                            'funcs': funcs }
                        gpios.append(pin)
            elif modulename == 'IO_QSPI':
                gpionameMatchString = r"^GPIO_QSPI_(?P<name>.*)_STATUS$"
                for r in m.findall('./registers/register'):
                    if r.find('description') is not None and r.find('description').text == 'GPIO status':
                        match = re.search(gpionameMatchString,r.find('name').text)
                        name = match.group('name').lower()
                        ctrl = m.find("./registers/register[name='GPIO_QSPI_"+name.upper()+"_CTRL']")
                        if ctrl is None:
                            LOGGER.error('Not found %s',name.upper())
                        func = ctrl.find("./fields/field[name='FUNCSEL']")
                        funcs = [];
                        for f in func.findall('./enumeratedValues/enumeratedValue'):
                            if f.find('name').text != 'null':
                                funcs.append({'name':f.find('name').text,'value':f.find('value').text})
                        status_offset = r.find('addressOffset').text
                        idx = int(int(status_offset[2:],16) / 8)
                        pin = {
                            'name':name,
                            'idx': idx,
                            'bank':'qspi',
                            'funcs': funcs }
                        gpios.append(pin)
            elif modulename == 'DMA':
                chMatchString = r"^CH(?P<name>\d+)_READ_ADDR$"
                for r in m.findall('./registers/register'):
                    match = re.search(chMatchString,r.find('name').text)
                    if match and match.group('name') is not None:
                        name = match.group('name').lower()
                        dma_channels.append({'name':name})
            elif modulename == 'CLOCKS':
                ctrlMatchString = r"^CLK_(?P<name>.+)_CTRL$"
                for r in m.findall('./registers/register'):
                    match = re.search(ctrlMatchString,r.find('name').text)
                    if match and match.group('name') is not None:
                        name = match.group('name').lower()
                        aux_fld = r.find("./fields/field[name='AUXSRC']")
                        if aux_fld is not None:
                            idx = int(int(r.find("addressOffset").text,16) / 12)
                            sources = []
                            aux_sel = 0
                            src_fld = r.find("./fields/field[name='SRC']")
                            if src_fld is not None:
                                for f in src_fld.findall('./enumeratedValues/enumeratedValue'):
                                    src_name = f.find('name').text
                                    if src_name == 'clksrc_clk_' + name + '_aux':
                                        aux_sel = f.find('value').text
                                    else:
                                        sources.append({'name':RPDeviceTree.make_clk_src_name(src_name),'src':f.find('value').text,'aux': 0})
                            for f in aux_fld.findall('./enumeratedValues/enumeratedValue'):
                                sources.append({'name':RPDeviceTree.make_clk_src_name(f.find('name').text),'src':aux_sel,'aux': f.find('value').text})
                            clk = {'name':name,'sources':sources,'glitchless':src_fld is not None, 'idx': idx}
                            clocks.append(clk)
            else:
                matchString = r"(?P<module>.*\D)(?P<instance>\d*$)"
                match = re.search(matchString, modulename)
                modules.append({'module': match.group("module").lower(), 'instance': modulename.lower()})

        p['modules'] = sorted(list(set([(m['module'], m['instance']) for m in modules])))
        p['gpios'] = gpios
        p['dma_channels'] = dma_channels
        p['clocks'] = clocks

        modules_map = {}
        modules_map['clocks'] = {'module': 'clocks', 'instance': 'clocks'}
        for m in modules:
            modules_map[m['instance']]=m

        for gpio in gpios:
            signals = []
            for func in gpio['funcs']:
                signals.append(RPDeviceTree.func_to_signal(modules_map,func))
            gpio['signals'] = signals

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

        LOGGER.debug("Available Modules are:\n" + RPDeviceTree._modulesToString(p['modules']))
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

        for section in p["memories"]:
            memory_section = core_child.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
        # sort the node children by start address and size
        core_child.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))


        for vector in p['interrupts']:
            if int(vector['position']) < 0: continue;
            vector_section = core_child.addChild('vector')
            vector_section.setAttributes(['position', 'name'], vector)
        core_child.addSortKey(lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, ""))

        modules = {}
        for m, i in p['modules']:
            # filter out non-peripherals: fuses, micro-trace buffer
            # gpio part
            if m in ['pads_bank', 'pads_qspi']: continue;
            # clock subsystem
            if m in ['pll_usb', 'pll_sys', 'xosc']: continue;
            # usb subsystem
            if m in ['usbctrl_regs', 'usbctrl_dpram']: continue;
            # xip subsystem
            if m in ['xip_ctrl']: continue;
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


        # add all GPIOs
        for pin in p['gpios']:
            pin_driver = gpio_driver.addChild('gpio')
            pin_driver.setAttributes(
                'port', pin['bank'], 
                'pin', str(pin['idx']),
                'name', pin['name'])
            for s in pin['signals']:
                signal = pin_driver.addChild('signal')
                signal.setAttributes('driver',s['driver'],'name',s['name'],'af',s['af'])
                if 'instance' in s:
                    signal.setAttribute('instance',s['instance'])
            pin_driver.addSortKey(lambda e: (e['af'],
                                             e['name']))

        # DMA driver
        dma_driver = tree.addChild('driver')
        dma_driver.setAttributes('name', 'dma', 'type', compatible)
        for ch in p['dma_channels']:
            ch_driver = dma_driver.addChild('channel')
            ch_driver.setAttributes(
                'name', ch['name'])
            ch_driver.addSortKey(lambda e: (-1,
                                             e['name']))

        # Clocks driver
        clocks_driver = tree.addChild('driver')
        clocks_driver.setAttributes('name', 'clocks', 'type', compatible)
        for clk in p['clocks']:
            clk_driver = clocks_driver.addChild('clock')
            clk_driver.setAttributes('name', clk['name'], 
                'glitchless', clk['glitchless'] and 'true' or 'false',
                'idx', clk['idx'])
            for src in clk['sources']:
                src_driver = clk_driver.addChild('source')
                src_driver.setAttributes('name', src['name'], 'src', src['src'], 'aux', src['aux'])

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
        p = RPDeviceTree._properties_from_file(str(filename))
        if p is None: return None;
        return RPDeviceTree._device_tree_from_properties(p)
