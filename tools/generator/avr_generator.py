#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import glob
import logging

import dfg.logger

from dfg.merger import DeviceMerger
from dfg.avr.avr_device_tree import AVRDeviceTree
from dfg.avr.avr_groups import avr_groups
from dfg.output.device_file import DeviceFileWriter

LOGGER = logging.getLogger('dfg.avr')

if __name__ == "__main__":
    devices = []
    loglevel = 'INFO'
    devs = []
    device_depth = 1e6

    for arg in sys.argv[1:]:
        if arg.startswith('--log='):
            loglevel = arg.replace('--log=', '')
            continue
        if arg.startswith('--depth='):
            device_depth = int(arg.replace('--depth=', '')) - 1
            continue
        devs.append(arg)

    dfg.logger.configure_logger(loglevel)

    for dev in devs:
        xml_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'AVR_devices', (dev + '*'))
        files = glob.glob(xml_path)
        for filename in files:
            # ATtiny28 is missing data, which is required by the device reader,
            # which makes us exclude this device.
            if os.path.basename(filename) != "ATtiny28.xml":
                device = AVRDeviceTree.from_file(filename)
                devices.append(device)
                if device_depth > 0:
                    device_depth -= 1
                else:
                    print(device.toString())
                    exit(1)

    mergedDevices = DeviceMerger.merge(avr_groups, devices)

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'avr')
    def filename(ids):
        p = {}
        for k in ids.keys():
            v = []
            for b in ids.getAttribute(k):
                if b == "": b = 'n';
                v.append(b)
            if k in ['type', 'pin']: v.sort();
            if len(v) > 0:
                p[k] = "_".join(v)

        fmt = "at{family}"
        index = DeviceMerger._get_index_for_id(avr_groups, ids[0])
        if index == -1:
            fmt += "-{name}-{type}"
        else:
            keys = avr_groups[index].keys()
            if 'name' in keys:
                fmt += "-{name}"
            if 'type' in keys:
                fmt += "-{type}"
            if 'pin' in keys:
                fmt += "-{pin}"
        return fmt.format(**p)

    for dev in mergedDevices:
        DeviceFileWriter.write(dev, folder, filename)
        # print(dev.toString())
