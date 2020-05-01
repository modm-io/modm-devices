#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.
# TESTING:  exec(open("./nrf_generator.py").read())

import argparse
from pathlib import Path

import dfg.logger
import dfg.generator
from dfg.nrf.nrf_device_tree import NRFDeviceTree
from dfg.nrf.nrf_groups import nrf_groups

arg = argparse.ArgumentParser(description="Device File Generator for NRF")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("--check-merge", default=False, action="store_true", help="Brute-force check the merge algorithm")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

devices = {}
for dev in args.filter:
    files = Path("raw-device-data/nrf-devices/nrf").glob(dev.lower() + "_*.ld")
    for filename in files:
        device = NRFDeviceTree.from_file(filename)
        if device is None: continue;
        devices[device.ids.string] = device

def filename(ids):
    p = {}
    for k in ids.keys():
        v = []
        for b in ids.getAttribute(k):
            v.append(b)
        if len(v) > 0:
            p[k] = "_".join(v)
    fmt = "{platform}{family}{series}"
    return fmt.format(**p)

dfg.generator.run(output="nrf", devices=devices, groups=nrf_groups,
                  filename=filename, check_merge=args.check_merge)

