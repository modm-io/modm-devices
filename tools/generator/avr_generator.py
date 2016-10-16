#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import glob

from dfg.logger import Logger

from dfg.device import Device
from dfg.merger import DeviceMerger
from dfg.avr.avr_reader import AVRDeviceReader
from dfg.avr.avr_writer import AVRDeviceWriter

if __name__ == "__main__":
    level = 'info'
    logger = Logger(level)
    devices = []

    for arg in sys.argv[1:]:
        if arg in ['error', 'warn', 'info', 'debug', 'disabled']:
            level = arg
            logger.setLogLevel(level)
            continue
        xml_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AVR_devices', (arg + '*'))
        files = glob.glob(xml_path)
        for file in files:
            # deal with this here, rather than rewrite half the name merging
            if os.path.basename(file) != "ATtiny28.xml":
                part = AVRDeviceReader(file, logger)
                device = Device(part, logger)
                devices.append(device)

    merger = DeviceMerger(devices, logger)
    merger.mergedByPlatform('avr')

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'avr')

    for dev in merger.mergedDevices:
        writer = AVRDeviceWriter(dev, logger)
        writer.write(folder)
