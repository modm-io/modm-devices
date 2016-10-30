#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import logging

import dfg.logger

from dfg.merger import DeviceMerger
from dfg.stm32.stm_device_tree import STMDeviceTree
from dfg.stm32.stm_groups import stm_groups
from dfg.output.device_file import DeviceFileWriter

LOGGER = logging.getLogger('dfg.stm')

if __name__ == "__main__":
    devices = []
    supported_families = ['STM32F0', 'STM32F1', 'STM32F2', 'STM32F3', 'STM32F4', 'STM32F7']
    filtered_family = None
    filtered_device = []
    loglevel = 'INFO'
    fams = []
    device_depth = 1e6

    for arg in sys.argv[1:]:
        if arg.startswith('--log='):
            loglevel = arg.replace('--log=', '')
            continue
        if arg.startswith('--depth='):
            device_depth = int(arg.replace('--depth=', '')) - 1
            continue
        fams.append(arg)

    dfg.logger.configure_logger(loglevel)

    for fam in fams:
        if any (fam.startswith(f) for f in supported_families):
            filtered_device.append(fam)
            filtered_family = fam[:7]
        else:
            LOGGER.error("Invalid family! Valid input is '{}', found '{}'".format(", ".join(supported_families), fam))
            exit(1)

    if len(filtered_device) == 0:
        LOGGER.error("Please provide a device family: '{}'".format(", ".join(supported_families)))
        exit(1)

    devicesFromFamily = STMDeviceTree.getDevicesFromFamily(filtered_family)

    for deviceName in [d for d in devicesFromFamily if any(d.startswith(fd) for fd in filtered_device)]:
        device = STMDeviceTree.from_partname(deviceName)
        devices.append(device)
        if device_depth > 0:
            device_depth -= 1
        else:
            print(device.toString())
            exit(1)

    mergedDevices = DeviceMerger.merge(stm_groups, devices)

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'stm32')
    def filename(ids):
        p = {}
        for k in ids.keys():
            v = ids.getAttribute(k)
            if len(v) > 0:
                p[k] = "_".join(v)

        fmt = "stm32f-{name}"
        index = DeviceMerger._get_index_for_id(stm_groups, ids[0])
        if index == -1 or 'size' in stm_groups[index].keys():
            fmt += "-{size}"
        return fmt.format(**p)

    for dev in mergedDevices:
        DeviceFileWriter.write(dev, folder, filename)
        # print(dev.toString())
