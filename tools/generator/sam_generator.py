#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.
# TESTING:  exec(open("./sam_generator.py").read())

import argparse
from pathlib import Path

import dfg.logger
import dfg.generator
from dfg.sam.sam_device_tree import SAMDeviceTree
from dfg.sam.sam_groups import sam_groups

arg = argparse.ArgumentParser(description="Device File Generator for SAM")
arg.add_argument("--log-level", default="INFO", nargs="?", choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLED"], help="Choose the output log level")
arg.add_argument("--check-merge", default=False, action="store_true", help="Brute-force check the merge algorithm")
arg.add_argument("filter", nargs = "*", help="Only consider devices starting with this string")
args = arg.parse_args()
dfg.logger.configure_logger(args.log_level)

devices = {}
for dev in args.filter:
    files = Path("raw-device-data/sam-devices/").glob('*/AT' + dev.upper() + '*')
    for filename in files:
        for dev in SAMDeviceTree.from_file(filename):
            if dev is None: continue;
            devices[dev.ids.string] = dev

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

dfg.generator.run(output="sam", devices=devices, groups=sam_groups,
                  filename=filename, check_merge=args.check_merge)
