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
from collections import defaultdict

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

filenames = {}
def filename(ids, extra=None):
    p = {}
    for k in ids.keys():
        v = ids.getAttribute(k)
        if len(v) > 0:
            p[k] = "_".join(v)
    fmt = "stm32{family}-{name}"
    for v in (extra or []): fmt += f"-{{{v}}}"
    return fmt.format(**p)


def filename_pre(ids, extra=None):
    index = DeviceMerger._get_index_for_id(stm_groups, ids[0])
    if index != -1:
        extra = list(sorted(set(stm_groups[index].keys()) - {"family", "name"}))
    return filename(ids, extra=extra), ids


def merger(merge_group, devices):
    mergeable = defaultdict(list)

    for device in devices:
        index = DeviceMerger._get_index_for_id(merge_group, device.ids[0])
        if index >= 0:
            mergeable[index].append(device)
        else:
            for child in device.children:
                if child.name == "attribute-die":
                    mergeable[child.attributes["value"]].append(device)

    result = []
    filenames_pre = defaultdict(list)
    for idx, group in mergeable.items():
        device = group[0]
        for d in group[1:]:
            device.merge(d)
        device._sortTree()
        result.append(device)
        name, ids = filename_pre(device.ids)
        filenames_pre[name].append(ids)

    extras_pre = ["size", "pin", "variant"]
    extras = []
    while len(filenames_pre):
        extras.append(extras_pre.pop(0))
        for name, ids_list in list(filenames_pre.items()):
            filenames_pre.pop(name)
            if len(ids_list) == 1:
                filenames[frozenset(ids_list[0])] = name
            else:
                for ids in ids_list:
                    name, ids = filename_pre(ids, extras)
                    filenames_pre[name].append(ids)

    return result


dfg.generator.run(output="stm32", devices=devices, groups=stm_groups,
                  filename=lambda ids: filenames[frozenset(ids)],
                  check_merge=args.check_merge, merger=merger)

