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
from dfg.avr.avr_device_tree import AVRDeviceTree
from dfg.avr.avr_groups import avr_groups

arg = argparse.ArgumentParser(description="Device File Generator for AVR")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("--check-merge", default=False, action="store_true", help="Brute-force check the merge algorithm")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

devices = {}
for dev in args.filter:
    files = Path("raw-device-data/avr-devices/").glob('*/AT' + dev + '*')
    for filename in files:
        for device in AVRDeviceTree.from_file(filename):
            if device is None: continue;
            devices[device.ids.string] = device

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

dfg.generator.run(output="avr", devices=devices, groups=avr_groups,
                  filename=filename, check_merge=args.check_merge)
