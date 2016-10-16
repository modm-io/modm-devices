#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import glob
import logging

import dfg.logger

from dfg.device import Device
from dfg.merger import DeviceMerger
from dfg.avr.avr_reader import AVRDeviceReader
from dfg.avr.avr_writer import AVRDeviceWriter

LOGGER = logging.getLogger('dfg.avr')

if __name__ == "__main__":
    devices = []
    loglevel = 'INFO'
    devs = []

    for arg in sys.argv[1:]:
        if arg.startswith('--log='):
            loglevel = arg.replace('--log=', '')
            continue
        devs.append(arg)

    dfg.logger.configure_logger(loglevel)

    for dev in devs:
        xml_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AVR_devices', (dev + '*'))
        files = glob.glob(xml_path)
        for file in files:
            # deal with this here, rather than rewrite half the name merging
            if os.path.basename(file) != "ATtiny28.xml":
                part = AVRDeviceReader(file)
                device = Device(part)
                devices.append(device)

    merger = DeviceMerger(devices)
    merger.mergedByPlatform('avr')

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'avr')

    for dev in merger.mergedDevices:
        writer = AVRDeviceWriter(dev)
        writer.write(folder)
