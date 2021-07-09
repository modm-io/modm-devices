#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import argparse
from pathlib import Path

import dfg.logger
import dfg.generator
from dfg.merger import DeviceMerger
from dfg.stm32.stm_device_tree import STMDeviceTree
from dfg.stm32.stm_groups import stm_groups

arg = argparse.ArgumentParser(description="Device File Memory Maps")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("--check-merge", default=False, action="store_true", help="Brute-force check the merge algorithm")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

deviceNames = []
for f in args.filter:
    deviceNames.extend(STMDeviceTree.getDevicesFromPrefix(f.upper()))
deviceNames = sorted(list(set(deviceNames)))

devices = {}
for deviceName in deviceNames:
    for device in STMDeviceTree.from_partname(deviceName):
        devices[device.ids.string] = device

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

dfg.generator.run(output="stm32", devices=devices, groups=stm_groups,
                  filename=filename, check_merge=args.check_merge)

