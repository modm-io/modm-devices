#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import glob
import logging

from ..device import Device
from .avr_reader import AVRDeviceReader

LOGGER = logging.getLOGGER('dfg.avr.registers')

if __name__ == "__main__":
    """
    Some test code
    """
    devices = []
    peri_name = "all"
    bitfield_pattern = ""

    for arg in sys.argv[1:]:
        if "ATtiny" in arg or "ATmega" in arg or 'AT90' in arg:
            xml_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'AVR_devices', (arg + '*'))
            files = glob.glob(xml_path)
            for file in files:
                # deal with this here, rather than rewrite half the name merging
                if os.path.basename(file) != "ATtiny28.xml":
                    part = AVRDeviceReader(file)
                    devices.append(Device(part))
            continue

        if any(arg.startswith(per) for per in ["EXT", "TWI", "USART", "SPI", "AD_CON", "USB", "CAN", "DA_CON", "USI", "TIMER", "PORT"]):
            peri_name = arg
            continue

        bitfield_pattern = arg

    LOGGER.setLogLevel('debug')

    peripherals = []
    for dev in devices:
        attributes = dev.getProperty('peripherals')
        for attribute in attributes.values:
            for peripheral in [p for p in attribute.value if p.name.startswith(peri_name)]:
                peripherals.append({'ids': [dev.id], 'peripheral': peripheral})

    registers = []
    for peri in peripherals:
        for reg in peri['peripheral'].registers:
            registers.append({'ids': list(peri['ids']), 'register': reg})

    registers.sort(key=lambda k : k['register'].name)
    merged = []

    while len(registers) > 0:
        current = registers[0]
        registers.remove(current)

        matches = []

        for peri in registers:
            if current['register'] == peri['register']:
                matches.append(peri)

        for match in matches:
            current['ids'].extend(match['ids'])
            registers.remove(match)

        if len(matches) == 0:
            LOGGER.warning("No match for register: " + current['register'].name + " of " + str([device_id.string for device_id in current['ids']]))

        merged.append(current)

    filtered_devices = []
    filtered_registers = []
    all_names = []

    for dev in merged:
        reg = dev['register']
        dev['ids'].sort(key=lambda k : (int(k.name or 0), k.type))
        all_names.extend([id.string for device_id in dev['ids']])
        if bitfield_pattern == "":
            filtered_registers.append(dev['register'].name)
            s = "Devices:\n"
            ii = 0
            for device_id in dev['ids']:
                s += device_id.string.replace("at", "") + "  \t"
                ii += 1
                if ii > 7:
                    ii = 0
                    s += "\n"
            LOGGER.debug(s)
            LOGGER.info(str(reg) + "\n")

        if reg.getFieldsWithPattern(bitfield_pattern) != None:
            filtered_registers.append(dev['register'].name)
            filtered_devices.append(dev)

    all_filtered_names = []
    if bitfield_pattern != "":
        LOGGER.info("Registers containing BitField pattern '" + bitfield_pattern + "':")
        for dev in filtered_devices:
            all_filtered_names.extend([device_id.string for device_id in dev['ids']])
            s = "Devices:\n"
            ii = 0
            for device_id in dev['ids']:
                s += device_id.string.replace("at", "") + "  \t"
                ii += 1
                if ii > 7:
                    ii = 0
                    s += "\n"
            LOGGER.debug(s)
            LOGGER.info(str(dev['register']) + "\n")

    filtered_registers = list(set(filtered_registers))
    filtered_registers.sort()

    LOGGER.info("Summary registers:")
    for name in filtered_registers:
        LOGGER.debug(name)
    LOGGER.info("Remaining devices:")
    all_names = set(all_names) - set(all_filtered_names)
    all_names = list(all_names)
    all_names.sort()
    s = "\n"
    ii = 0
    for device_id in all_names:
        s += device_id.replace("at", "") + "  \t"
        ii += 1
        if ii > 7:
            ii = 0
            s += "\n"
    LOGGER.debug(s)
