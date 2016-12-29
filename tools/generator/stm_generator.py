#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import sys
import logging
import argparse
from pathlib import Path

import dfg.logger

from dfg.merger import DeviceMerger
from dfg.stm32.stm_device_tree import STMDeviceTree
from dfg.stm32.stm_groups import stm_groups
from dfg.output.device_file import DeviceFileWriter
from modm.parser import DeviceParser
from deepdiff import DeepDiff

LOGGER = logging.getLogger("dfg.stm")

arg = argparse.ArgumentParser(description="Device File Memory Maps")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

deviceNames = []
for f in args.filter:
    deviceNames.extend(STMDeviceTree.getDevicesFromPrefix(f))
deviceNames = sorted(list(set(deviceNames)))

devices = {}
for deviceName in deviceNames:
    device = STMDeviceTree.from_partname(deviceName)
    if device is None: continue;
    devices[device.ids.string] = device

mergedDevices = DeviceMerger.merge(stm_groups, [d.copy() for d in devices.values()])

def filename(ids):
    p = {}
    for k in ids.keys():
        v = ids.getAttribute(k)
        if len(v) > 0:
            p[k] = "_".join(v)
    fmt = "stm32{family}-{name}"
    index = DeviceMerger._get_index_for_id(stm_groups, ids[0])
    if index == -1 or "size" in stm_groups[index].keys():
        fmt += "-{size}"
    if index == -1 or "pin" in stm_groups[index].keys():
        fmt += "-{pin}"
    return fmt.format(**p)

folder = Path(os.path.realpath(__file__)).parents[2] / "devices" / "stm32"
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

tmp_folder = Path(os.path.realpath(__file__)).parent / "single"
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
