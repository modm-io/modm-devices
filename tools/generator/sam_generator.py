#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.
# TESTING:  exec(open("./sam_generator.py").read())

import os
import sys
import glob
import logging

import dfg.logger

from dfg.merger import DeviceMerger
from dfg.sam.sam_device_tree import SAMDeviceTree
from dfg.sam.sam_groups import sam_groups
from dfg.output.device_file import DeviceFileWriter
from modm_devices.parser import DeviceParser
from deepdiff import DeepDiff

LOGGER = logging.getLogger('dfg.sam')

if __name__ == "__main__":
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

    if not len(devs):
        devs.append('saml21')

    dfg.logger.configure_logger(loglevel)

    devices = {}
    for dev in devs:
        xml_path = os.path.join(os.path.dirname(__file__), 'raw-device-data', 'sam-devices', '*', ('AT' + dev.upper() + '*'))
        files = glob.glob(xml_path)
        for filename in files:
            for dev in SAMDeviceTree.from_file(filename):
                devices[dev.ids.string] = dev
                if device_depth > 0:
                    device_depth -= 1
                else:
                    print(device.toString())
                    exit(1)

    mergedDevices = DeviceMerger.merge(sam_groups, [d.copy() for d in devices.values()])

    def filename(ids):
        p = {}
        for k in ids.keys():
            v = []
            for b in ids.getAttribute(k):
                if b == "": b = 'n'
                v.append(b)
            if k in ['type', 'pin']: v.sort()
            if len(v) > 0:
                p[k] = "_".join(v)
        fmt = "{platform}{family}{series}"
        return fmt.format(**p)

    folder = os.path.join(os.path.dirname(__file__), '..', '..', 'devices', 'sam')
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
