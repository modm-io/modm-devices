#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import logging

import dfg.logger

from dfg.device import Device
from dfg.merger import DeviceMerger
from dfg.stm32.stm_reader import STMDeviceReader
from dfg.stm32.stm_writer import STMDeviceWriter

LOGGER = logging.getLogger('dfg.stm')

if __name__ == "__main__":
    devices = []
    supported_families = ['STM32F0', 'STM32F1', 'STM32F2', 'STM32F3', 'STM32F4', 'STM32F7']
    filtered_family = None
    filtered_device = None
    loglevel = 'INFO'
    fams = []

    for arg in sys.argv[1:]:
        if arg.startswith('--log='):
            loglevel = arg.replace('--log=', '')
            continue
        fams.append(arg)

    dfg.logger.configure_logger(loglevel)

    for fam in fams:
        if any (fam.startswith(f) for f in supported_families):
            filtered_device = fam
            filtered_family = fam[:7]
        else:
            LOGGER.error("Invalid family! Valid input is '{}', found '{}'".format(", ".join(supported_families), fam))
            exit(1)

    if filtered_device is None:
        LOGGER.error("Please provide a device family: '{}'".format(", ".join(supported_families)))
        exit(1)

    devicesFromFamily = STMDeviceReader.getDevicesFromFamily(filtered_family)

    for deviceName in [d for d in devicesFromFamily if d.startswith(filtered_device)]:
        device = STMDeviceReader(deviceName)
        devices.append(Device(device))

    merger = DeviceMerger(devices)
    merger.mergedByPlatform('stm32')

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'stm32')

    for dev in merger.mergedDevices:
        writer = STMDeviceWriter(dev)
        writer.write(folder)
