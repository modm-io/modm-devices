# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import re
import logging

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .stm_identifier import STMIdentifier
from . import stm

LOGGER = logging.getLogger('dfg.stm.reader')

class STMDeviceTree:
    """ STMDeviceTree
    This STM specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """
    rootpath = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'STM_devices', 'mcu')
    familyFile = XMLReader(os.path.join(rootpath, 'families.xml'))

    @staticmethod
    def getDevicesFromFamily(family, rootpath=None):
        rawDevices = STMDeviceTree.familyFile.query("//Family[@Name='{}']/SubFamily/Mcu/@RefName".format(family))
        # devices can contain duplicates due to Hx, Tx, Yx, Ix suffix!
        # we treat them as single devices, since we don't care about the MCUs package
        devices = []
        for dev in sorted(rawDevices):
            shortDev = dev[:-1] if dev.endswith('x') else dev
            LOGGER.debug("%s:%s", dev, shortDev)
            if all(not d.startswith(shortDev) for d in devices):
                devices.append(dev)

        LOGGER.debug("Found devices of family '{}': {}".format(family, ", ".join(devices)))
        return devices

    @staticmethod
    def _properties_from_partname(partname):
        deviceNames = STMDeviceTree.familyFile.query("//Family/SubFamily/Mcu[starts-with(@RefName,'{}')]".format(partname))
        # if len(deviceNames) > 1:
        #     LOGGER.error("Duplicate device files for '%s': %s", partname, [d.get('Name') for d in deviceNames])
        comboDeviceName = deviceNames[0].get('Name')
        device_file = XMLReader(os.path.join(STMDeviceTree.rootpath, comboDeviceName + '.xml'))
        properties = {}
        did = STMIdentifier.from_string(partname.lower())
        properties['id'] = did

        LOGGER.info("Parsing '%s'", did.string)

        # information about the core and architecture
        coreLut = {'m0': 'v6m', 'm3': 'v7m', 'm4': 'v7em', 'm7': 'v7em'}
        core = device_file.query('//Core')[0].text.replace('ARM ', '').lower()
        properties['architecture'] = coreLut[core.replace('cortex-', '')]
        if core.endswith('m4') or core.endswith('m7'):
            core += 'f'
        if did["family"] in ['f7'] and did["name"] not in ['745', '746', '756']:
            core += 'd'
        properties['core'] = core

        # flash and ram sizes
        # The <ram> and <flash> can occur multiple times.
        # they are "ordered" in the same way as the `(S-I-Z-E)` ids in the device combo name
        # we must first find out which index the current did["size"] has inside `(S-I-Z-E)`
        sizeIndexFlash = 0
        sizeIndexRam = 0

        match = re.search("\(.(-.)*\)", comboDeviceName)
        if match:
            sizeArray = match.group(0)[1:-1].lower().split("-")
            sizeIndexFlash = sizeArray.index(did["size"])
            sizeIndexRam = sizeIndexFlash

        rams = sorted([int(r.text) for r in device_file.query("//Ram")])
        if sizeIndexRam >= len(rams):
            sizeIndexRam = len(rams) - 1

        flashs = sorted([int(f.text) for f in device_file.query("//Flash")])
        if sizeIndexFlash >= len(flashs):
            sizeIndexFlash = len(flashs) - 1

        mem_start, mem_model = stm.getMemoryForDevice(did)
        total_ram = ram = rams[sizeIndexRam] + mem_model['sram1']
        flash = flashs[sizeIndexFlash] + mem_model['flash']
        if 'ccm' in mem_model:
            total_ram += mem_model['ccm']
        if 'backup' in mem_model:
            total_ram += mem_model['backup']
        if 'itcm' in mem_model:
            total_ram += mem_model['itcm']
            total_ram += mem_model['dtcm']
        properties['ram'] = total_ram * 1024
        properties['flash'] = flash * 1024

        memories = []
        # first get the real SRAM1 size
        for mem, val in mem_model.items():
            if any(s in mem for s in ['2', '3', 'dtcm']):
                ram -= val

        # add all memories
        for mem, val in mem_model.items():
            if '1' in mem:
                memories.append({'name': 'sram1',
                                 'access' : 'rwx',
                                 'start': "0x{:02X}".format(mem_start['sram']),
                                 'size': str(ram)})
            elif '2' in mem:
                memories.append({'name': 'sram2',
                                 'access' : 'rwx',
                                 'start': "0x{:02X}".format(mem_start['sram'] + ram * 1024),
                                 'size': str(val)})
            elif '3' in mem:
                memories.append({'name': 'sram3',
                                 'access': 'rwx',
                                 'start': "0x{:02X}".format(mem_start['sram'] + ram * 1024 + mem_model['sram2'] * 1024),
                                 'size': str(val)})
            elif 'flash' in mem:
                memories.append({'name': 'flash',
                                 'access': 'rx',
                                 'start': "0x{:02X}".format(mem_start['flash']),
                                 'size': str(flash)})
            else:
                memories.append({'name': mem,
                                 'access': 'rw' if did["family"] == 'f4' and mem == 'ccm' else 'rwx',
                                 'start': "0x{:02X}".format(mem_start[mem]),
                                 'size': str(val)})

        properties['memories'] = memories

        # packaging
        package = device_file.query("//@Package")[0]
        properties['pin-count'] = re.findall('[0-9]+', package)[0]
        properties['package'] = re.findall('[A-Za-z\.]+', package)[0]

        # device header
        properties['header'] = 'stm32' + did["family"] + 'xx.h'

        # device defines
        defines = []

        dev_def = stm.getDefineForDevice(did)
        if dev_def is None:
            LOGGER.error("Define not found for device '{}'".format(did.string))
        else:
            defines.append(dev_def)

        properties['define'] = defines


        gpios = []
        properties['gpios'] = gpios
        gpio_afs = []
        properties['gpio_afs'] = gpio_afs
        peripherals = []
        properties['peripherals'] = peripherals
        modules = []
        properties['modules'] = modules

        omodules = device_file.query("//IP/@InstanceName")
        omodules = sorted(list(set(omodules)))
        LOGGER.debug("Available Modules are:\n" + STMDeviceTree._modulesToString(omodules))

        # add entire interrupt vectore table here.
        # I have not found a way to extract the correct vector _position_ from the ST device files
        # so we have to swallow our pride and just parse the header file
        # ext/cmsis/stm32/Device/ST/STM32F4xx/Include/
        headerFilePath = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'modm', 'ext', 'st', 'stm32{}xx'.format(did["family"]), 'Include', '{}.h'.format(dev_def.lower()))
        with open(headerFilePath, 'r') as headerFile:
            match = re.search("typedef enum.*?/\*\*.*?/\*\*.*?\*/(?P<table>.*?)} IRQn_Type;", headerFile.read(), re.DOTALL)
            if not match:
                LOGGER.error("Interrupt vector table not found for device '{}'".format(did.string))
                exit(1)

            # print dev_def.lower(), match.group('table')

            ivectors = []
            for line in match.group('table').split('\n')[1:-1]:
                if '=' not in line:  # avoid multiline comment
                    continue

                name, pos = line.split('/*!<')[0].split('=')
                pos = int(pos.strip(' ,'))
                name = name.strip()[:-5]
                if did["family"] in ['f3'] and pos == 42 and name == 'USBWakeUp':
                    continue
                ivectors.append({'position': pos, 'name': name})

            LOGGER.debug("Found interrupt vectors:\n" + "\n".join(["{}: {}".format(v['position'], v['name']) for v in ivectors]))
            properties['interrupts'] = ivectors

        for m in omodules:
            if any(m.startswith(per) for per in ['TIM', 'UART', 'USART', 'ADC', 'CAN', 'SPI', 'I2C', 'FSMC', 'FMC', 'RNG', 'RCC', 'USB']):
                modules.append(m)

        if 'CAN' in modules:
            modules.append('CAN1')

        if did["family"] in ['f2', 'f3', 'f4', 'f7']:
            modules.append('ID')

        dmaFile = None
        if 'DMA' in omodules:
            # lets load additional information about the DMA
            dma_file = device_file.query("//IP[@Name='DMA']")[0].get('Version')
            dma_file = os.path.join(STMDeviceTree.rootpath, 'IP', 'DMA-' + dma_file + '_Modes.xml')
            dmaFile = XMLReader(dma_file)
            dmas = [d.get('Name') for d in dmaFile.query("//IP/ModeLogicOperator/Mode[starts-with(@Name,'DMA')]")]
            modules.extend(dmas)

        invertMode = {'out': 'in', 'in': 'out', 'io': 'io'}
        nameToMode = {'rx': 'in', 'tx': 'out', 'cts': 'in', 'rts': 'out', 'ck': 'out',  # Uart
                     'miso': 'in', 'mosi': 'out', 'nss': 'io', 'sck': 'out',  # Spi
                     'scl': 'out', 'sda': 'io'}  # I2c

        # lets load additional information about the GPIO IP
        ip_file = device_file.query("//IP[@Name='GPIO']")[0].get('Version')
        ip_file = os.path.join(STMDeviceTree.rootpath, 'IP', 'GPIO-' + ip_file + '_Modes.xml')
        gpioFile = XMLReader(ip_file)

        pins = device_file.query("//Pin[@Type='I/O'][starts-with(@Name,'P')]")
        pins = sorted(pins, key=lambda p: [p.get('Name')[1:2], int(p.get('Name')[:4].split('-')[0].split('/')[0][2:])])

        for pin in pins:
            name = pin.get('Name')
            # F1 does not have pin 'alternate functions' only pin 'remaps' which switch groups of pins
            if did["family"] == 'f1':
                pinSignals = gpioFile.compactQuery("//GPIO_Pin[@Name='{}']/PinSignal/RemapBlock/..".format(name))
                rawAltFunctions = {a.get('Name'): a[0].get('Name')[-1:] for a in pinSignals}
                altFunctions = {}
                for alt_name in rawAltFunctions:
                    key = alt_name.split('_')[0].lower()
                    if key not in stm.stm32f1_remaps:
                        key += alt_name.split('_')[1].lower()
                    if key in stm.stm32f1_remaps:
                        mask = stm.stm32f1_remaps[key]['mask']
                        pos = stm.stm32f1_remaps[key]['position']
                        value = stm.stm32f1_remaps[key]['mapping'][int(rawAltFunctions[alt_name])]
                        altFunctions[alt_name] = '{},{},{}'.format(pos, mask, value)
                # Add the rest of the pins
                allSignals = device_file.compactQuery("//Pin[@Name='{}']/Signal".format(name))
                for sig in allSignals:
                    if not any(sig.get('Name') in name.get('Name') for name in pinSignals):
                        pinSignals.append(sig)

            else:  # F0, F3, F4 and F7
                pinSignals = gpioFile.compactQuery("//GPIO_Pin[@Name='%s']/PinSignal/SpecificParameter[@Name='GPIO_AF']/.." % name)
                altFunctions = { a.get('Name') : a[0][0].text.replace('GPIO_AF', '')[:2].replace('_', '') for a in pinSignals }

                # the analog channels are only available in the Mcu file, not the GPIO file
                analogSignals = device_file.compactQuery("//Pin[@Name='{}']/Signal[starts-with(@Name,'ADC')]".format(name))
                pinSignals.extend(analogSignals)

            name = name[:4].split('-')[0].split('/')[0].strip()

            gpio = {'port': name[1:2], 'id': name[2:]}
            gpios.append(gpio)

            afs = []

            for signal in [s.get('Name') for s in pinSignals]:
                raw_names = signal.split('_')
                if len(raw_names) < 2:
                    continue

                if not any(m.startswith(raw_names[0]) for m in modules):
                    continue

                instance = raw_names[0][-1]
                if not instance.isdigit():
                    instance = ""

                name = raw_names[1].lower()
                mode = None
                if name in nameToMode and nameToMode[name] != 'io':
                    mode = nameToMode[name]
                af_id = None
                if signal in altFunctions:
                    af_id = altFunctions[signal]

                if signal.startswith('USART') or signal.startswith('UART'):
                    af = {'peripheral' : 'Uart' + instance,
                          'name': name.capitalize()}
                    if mode:
                        af.update({'type': mode})
                    if af_id:
                        af.update({'id': af_id})
                    afs.append(af)

                    mapName = {'rx': 'miso', 'tx': 'mosi', 'ck': 'sck'}
                    if signal.startswith('USART') and name in mapName:
                        af = {'peripheral' : 'UartSpiMaster' + instance,
                              'name': mapName[name].capitalize()}
                        if mode:
                            af.update({'type': mode})
                        if af_id:
                            af.update({'id': af_id})
                        afs.append(af)

                elif signal.startswith('SPI'):
                    af = {'peripheral' : 'SpiMaster' + instance,
                          'name': name.capitalize()}
                    if mode:
                        af.update({'type': mode})
                    if af_id:
                        af.update({'id': af_id})
                    afs.append(dict(af))
                    # invertName = {'miso': 'somi', 'mosi': 'simo', 'nss': 'nss', 'sck': 'sck'}
                    # af.update({   'peripheral' : 'SpiSlave' + instance,
                    #           'name': invertName[name].capitalize()})
                    # if mode:
                    #   af.update({'type': invertMode[nameToMode[name]]})
                    # afs.append(af)

                if signal.startswith('CAN'):
                    if instance == '':
                        instance = '1'
                    af = {'peripheral' : 'Can' + instance,
                          'name': name.capitalize()}
                    if mode:
                        af.update({'type': mode})
                    if af_id:
                        af.update({'id': af_id})
                    afs.append(af)

                if signal.startswith('RCC'):
                    if 'MCO' in signal:
                        device_id = "" if len(raw_names) < 3 else raw_names[2]
                        af = {'peripheral': 'ClockOutput' + device_id}
                        af.update({'type': 'out'})
                        if af_id:
                            af.update({'id': af_id})
                        afs.append(af)

                if signal.startswith('I2C'):
                    if name in ['scl', 'sda']:
                        af = {'peripheral' : 'I2cMaster' + instance,
                              'name': name.capitalize()}
                        if mode:
                            af.update({'type': mode})
                        if af_id:
                            af.update({'id': af_id})
                        afs.append(af)

                if signal.startswith('TIM'):
                    for tname in raw_names[1:]:
                        tinstance = raw_names[0].replace('TIM', '')
                        nice_name = 'ExternalTrigger'
                        output_type = 'in'
                        if 'CH' in tname:
                            nice_name = tname.replace('CH', 'Channel')
                            output_type = None
                        elif 'BKIN' in tname:
                            nice_name = 'BreakIn'
                        af = {'peripheral' : 'Timer' + tinstance,
                              'name': nice_name}
                        if output_type:
                            af.update({'type': output_type})
                        if af_id:
                            af.update({'id': af_id})
                        afs.append(af)

                if signal.startswith('ADC'):
                    if 'exti' not in name:
                        af = {'peripheral' : 'Adc' + instance,
                              'name': name.replace('in', 'Channel').capitalize(),
                              'type': 'analog'}
                        afs.append(af)

                if signal.startswith('SYS'):
                    if 'mco' in name:
                        af = {'peripheral' : signal.replace('SYS', '').replace('_', ''),
                              'type': 'out',
                              'id': '0'}
                        afs.append(af)

                if signal.startswith('USB_OTG_FS') and raw_names[3] in ['DM', 'DP']:
                    af = {'peripheral' : 'Usb',
                          'name': raw_names[3].capitalize()}
                    if af_id:
                        af.update({'id': af_id})
                    else:
                        af.update({'id': '10'})
                    afs.append(af)

                if signal.startswith('USB_') and raw_names[1] in ['DM', 'DP']:
                    af = {'peripheral': 'Usb',
                          'name': raw_names[1].capitalize()}
                    if af_id:
                        af.update({'id': af_id})
                    # For the STM32F1 the USB pins aren't enabled like other
                    # alternative functions, but by simply enabling the USB core.
                    # else:
                    #   af.update({'id': '10'})
                    afs.append(af)

                if signal.startswith('FSMC_') or signal.startswith('FMC_'):
                    if not raw_names[1].startswith('DA'):
                        af = {'peripheral' : 'Fsmc',
                              'name': raw_names[1].capitalize()}
                        if af_id:
                            af.update({'id': af_id})
                        afs.append(af)

            # sort after key id and then add all without ids
            # this sorting only affect the way the debug information is displayed
            # in stm_writer the AFs are sorted again anyway
            sorted_afs = [a for a in afs if 'id' in a]
            sorted_afs.sort(key=lambda k: (int(k['id'].split(',')[0]), k['peripheral']))
            sorted_afs.extend([a for a in afs if 'id' not in a])

            for af in sorted_afs:
                af['gpio_port'] = gpio['port']
                af['gpio_id'] = gpio['id']
                gpio_afs.append(af)

        if 'CAN' in modules:
            modules.remove('CAN')

        return properties

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
    def _device_tree_from_properties(p):
        tree = DeviceTree('device')
        tree.ids.append(p['id'])
        LOGGER.info(("Generating Device Tree for '%s'" % p['id'].string))

        def topLevelOrder(e):
            order = ['attribute-flash', 'attribute-ram', 'attribute-core', 'header', 'attribute-define']
            if e.name in order:
                if e.name in ['attribute-flash', 'attribute-ram']:
                    return (order.index(e.name), int(e['value']))
                else:
                    return (order.index(e.name), e['value'])
            return (len(order), -1)
        tree.addSortKey(topLevelOrder)

        STMDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-flash')
        STMDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-ram')
        STMDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-core')
        # STMDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-pin-count')
        STMDeviceTree.addDeviceAttributesToNode(p, tree, 'header')
        STMDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-define')

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
        core_child.setAttributes('type', 'core', 'compatible', 'cortex')
        core_child.setIdentifier(lambda e: e['type'] + e['compatible'])

        # Memories
        STMDeviceTree.addMemoryToNode(p, core_child)
        STMDeviceTree.addInterruptTableToNode(p, core_child)

        adc_map = {'f0': 'stm32f0',
                   'f1': 'stm32f1',
                   'f2': 'stm32f2',
                   'f3': 'stm32f3',
                   'f4': 'stm32',
                   'f7': 'stm32'}
        # ADC
        if p['id']["family"] == 'f3' and p['id']["name"] == '373':
            STMDeviceTree.addModuleAttributesToNode(p, tree, 'ADC', 'adc', 'stm32')
        else:
            STMDeviceTree.addModuleAttributesToNode(p, tree, 'ADC', 'adc', adc_map[p['id']["family"]])
        # CAN
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'CAN', 'can')
        # Clock
        clock_child = tree.addChild('driver')
        clock_child.setAttributes('type', 'clock', 'compatible', 'stm32')
        clock_child.setIdentifier(lambda e: e['type'] + e['compatible'])
        # DAC
        # STMDeviceTree.addModuleAttributesToNode(p, tree, 'DAC', 'dac')
        # DMA
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'DMA', 'dma', 'stm32')
        # FSMC
        STMDeviceTree.addModuleAttributesToNode(p, tree, ['FMC', 'FSMC'], 'fsmc')
        # I2C
        i2c_map = {'f0': 'stm32f0',
                   'f1': 'stm32',
                   'f2': 'stm32',
                   'f3': 'stm32f3',
                   'f4': 'stm32',
                   'f7': 'stm32'}
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'I2C', 'i2c', i2c_map[p['id']["family"]])
        # return
        # ID
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'ID', 'id')
        # Random
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'RNG', 'random')
        # SPI
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'SPI', 'spi')
        STMDeviceTree.addModuleAttributesToNode(p, tree, ['UART', 'USART'], 'spi', 'stm32_uart')
        # Timer
        STMDeviceTree.addModuleAttributesToNode(p, tree, 'TIM', 'timer')
        # UART
        STMDeviceTree.addModuleAttributesToNode(p, tree, ['UART', 'USART'], 'uart')
        # USB
        STMDeviceTree.addModuleAttributesToNode(p, tree, ['OTG_FS_DEVICE', 'USB_FS', 'OTG_FS', 'USB'], 'usb', 'stm32_fs')
        # GPIO
        STMDeviceTree.addGpioToNode(p, tree)

        return tree


    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split('-')[-1]
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setAttribute('value', prop)
            child.setIdentifier(lambda e: e.name)

    @staticmethod
    def addMemoryToNode(p, node):
        for section in p['memories']:
            memory_section = node.addChild('memory')
            memory_section.setAttributes(['name', 'access', 'start', 'size'], section)
            memory_section.setIdentifier(lambda e: e['name'])
        # sort the node children by start address and size
        node.addSortKey(lambda e: (int(e['start'], 16), int(e['size'])) if e.name == 'memory' else (-1, -1))

    @staticmethod
    def addInterruptTableToNode(p, node):
        interrupts = p['interrupts']

        for vector in interrupts:
            vector_section = node.addChild('vector')
            vector_section.setAttributes(['position', 'name'], vector)
            vector_section.setIdentifier(lambda e: e['position'])
        # sort the node children by vector number and name
        node.addSortKey(lambda e: (int(e['position']), e['name']) if e.name == 'vector' else (-1, ""))

    @staticmethod
    def addModuleAttributesToNode(p, node, peripheral, name, family='stm32'):
        modules = p['modules']

        peripherals = []
        if isinstance(peripheral, list):
            peripherals.extend(peripheral)
        else:
            peripherals.append(peripheral)

        driver = node.addChild('driver')
        driver.setAttributes('type', name, 'compatible', family)
        driver.addSortKey(lambda e: int(e['value']))
        driver.setIdentifier(lambda e: e['type'] + e['compatible'])

        for module in modules:
            instances = []
            found = False
            for p in peripherals:
                if module.startswith(p):
                    found = True
                    inst = module[len(p):]
                    if inst != '' and inst.isdigit():
                        instances.append(inst)

            if not found:
                continue
            for instance in instances:
                child = driver.addChild('instance')
                child.setAttribute('value', instance)
                child.setIdentifier(lambda e: e.name)

    @staticmethod
    def addGpioToNode(p, node):
        gpios = p['gpios']

        driver = node.addChild('driver')
        driver.setAttributes('type', 'gpio', 'compatible', 'stm32f1' if p['id']["family"] == 'f1' else 'stm32')
        driver.setIdentifier(lambda e: e['type'] + e['compatible'])

        for gpio in gpios:
            gpio_child = driver.addChild('gpio')
            gpio_child.setAttributes(['port', 'id'], gpio)
            gpio_child.setIdentifier(lambda e: e['port'] + e['id'])
            # search for alternate functions
            matches = []
            for af in p['gpio_afs']:
                if af['gpio_port'] == gpio['port'] and af['gpio_id'] == gpio['id']:
                    af_child = gpio_child.addChild('af')
                    af_child.setIdentifier(lambda e: e['peripheral'] + e['name'])
                    af_child.setAttributes(['id', 'peripheral', 'name', 'type'], af)
            if p['id']["family"] == 'f1':
                gpio_child.addSortKey(lambda e : (int(e['id'].split(',')[0]) if e['id'] else 1e6, e['peripheral'] if e['peripheral'] else "", e['name']))
            else:
                gpio_child.addSortKey(lambda e : (int(e['id']) if e['id'] else 1e6, e['peripheral'] if e['peripheral'] else "", e['name']))
        # sort the node children by port and id
        driver.addSortKey(lambda e : (e['port'], int(e['id'])))

    @staticmethod
    def _hasCoreCoupledMemory(p):
        for memory in [memory.value for memory in p['memories'].values]:
            if any(mem['name'] == 'ccm' for mem in memory):
                return True
        return False

    @staticmethod
    def from_partname(partname):
        p = STMDeviceTree._properties_from_partname(partname)
        return STMDeviceTree._device_tree_from_properties(p)
