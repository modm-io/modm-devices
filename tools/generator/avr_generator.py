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
from modm_devices.parser import DeviceParser
from deepdiff import DeepDiff

LOGGER = logging.getLogger('dfg.avr')

if __name__ == "__main__":
    devices = {}
    loglevel = 'INFO'
    devs = []
    device_depth = 1e6
    simulate = False

    for arg in sys.argv[1:]:
        if arg.startswith('-n'):
            simulate = True
            continue
        if arg.startswith('--log='):
            loglevel = arg.replace('--log=', '')
            continue
        if arg.startswith('--depth='):
            device_depth = int(arg.replace('--depth=', '')) - 1
            continue
        devs.append(arg)

    dfg.logger.configure_logger(loglevel)

    for dev in devs:
        xml_path = os.path.join(os.path.dirname(__file__), 'raw-device-data', 'avr-devices', '*', (dev + '*'))
        files = glob.glob(xml_path)
        for filename in files:
            for dev in AVRDeviceTree.from_file(filename):
                devices[dev.ids.string] = dev
                if device_depth > 0:
                    device_depth -= 1
                else:
                    print(dev.toString())
                    exit(1)

    mergedDevices = DeviceMerger.merge(avr_groups, [d.copy() for d in devices.values()])

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

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'avr')
    parser = DeviceParser()
    parsed_devices = {}
    for dev in mergedDevices:
        # dump the merged device file into the devices folder
        path = DeviceFileWriter.write(dev, folder, filename)
        # immediately parse this file
        device_file = parser.parse(path)
        for device in device_file.get_devices():
            # and extract all the devices from it
            parsed_devices[device.partname] = device

    tmp_folder = os.path.join(os.path.dirname(__file__), 'single')
    os.makedirs(tmp_folder, exist_ok=True)
    for pname, pdevice in parsed_devices.items():
        # these are the properties from the merged device
        pprops = pdevice.properties
        # dump the associated single device
        rpath = DeviceFileWriter.write(devices[pname], tmp_folder, lambda ids: ids.string)
        # parse it again
        rdevice_file = parser.parse(rpath)
        rdevice = rdevice_file.get_devices()
        assert(len(rdevice) == 1)
        # these are the properties of the single device
        rprops = rdevice[0].properties
        ddiff = DeepDiff(rprops, pprops, ignore_order=True)
        # assert that there is no difference between the two
        assert(len(ddiff) == 0)
