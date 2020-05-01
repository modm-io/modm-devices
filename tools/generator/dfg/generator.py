#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.
# TESTING:  exec(open("./sam_generator.py").read())

from pathlib import Path
from .merger import DeviceMerger
from .output.device_file import DeviceFileWriter
from modm_devices.parser import DeviceParser

def run(output, devices, groups, filename, check_merge=False):
    def localpath(path):
        return Path(__file__).resolve().parents[1] / path

    if check_merge:
        devs_to_merge = (d.copy() for d in devices.values())
    else:
        devs_to_merge = devices.values()
    mergedDevices = DeviceMerger.merge(groups, devs_to_merge)

    output = localpath("../../devices/") / output
    parser = DeviceParser()
    parsed_devices = {}
    for dev in mergedDevices:
        # dump the merged device file into the devices folder
        path = DeviceFileWriter.write(dev, output, filename)
        if check_merge:
            # immediately parse this file
            device_file = parser.parse(path)
            for device in device_file.get_devices():
                # and extract all the devices from it
                parsed_devices[device.partname] = device

    if check_merge:
        from deepdiff import DeepDiff
        tmp_folder = localpath("single")
        tmp_folder.mkdir(parents=True, exist_ok=True)
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
