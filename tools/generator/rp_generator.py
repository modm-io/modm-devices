#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# Copyright (c)      2022, Andrey Kunitsyn
# All rights reserved.
# TESTING:  exec(open("./pr_generator.py").read())

import argparse
from pathlib import Path

import dfg.logger
import dfg.generator
from dfg.rp.rp_device_tree import RPDeviceTree
from dfg.rp.rp_groups import rp_groups

arg = argparse.ArgumentParser(description="Device File Generator for RP")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("--check-merge", default=False, action="store_true", help="Brute-force check the merge algorithm")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

devices = {}
for dev in args.filter:
    files = Path("raw-device-data/rp-devices").glob(dev.lower() + "*.svd")
    for filename in files:
        device = RPDeviceTree.from_file(filename)
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
    fmt = "{platform}{family}{ram}{flash}"
    return fmt.format(**p)

dfg.generator.run(output="rp", devices=devices, groups=rp_groups,
                  filename=filename, check_merge=args.check_merge)

