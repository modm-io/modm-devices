# Copyright 2013, Niklas Hauser
# Copyright 2016, Fabian Greif
# SPDX-License-Identifier: MPL-2.0

import logging
from collections import defaultdict

from modm_data import cubemx
from .tree import DeviceTree
from .merger import group_index

LOGGER = logging.getLogger(__name__)
PLATFORM = "stm32"

# Devices matching a merge group are merged, otherwise devices with the same die are merged
stm_groups = [
    {"family": ["c0"], "name": ["11", "31"]},
    {"family": ["c0"], "name": ["51", "71"]},
    {"family": ["f0"], "name": ["30"]},
    {"family": ["f0"], "name": ["70"]},
    {"family": ["f3"], "name": ["01"]},
    {"family": ["f3"], "name": ["02"], "size": ["6", "8"]},
    {"family": ["f3"], "name": ["02"], "size": ["b", "c", "d", "e"]},
    {"family": ["f3"], "name": ["03"], "size": ["6", "8"]},
    {"family": ["f3"], "name": ["03"], "size": ["b", "c", "d", "e"]},
    {"family": ["f3"], "name": ["58", "98"]},
    {"family": ["f4"], "name": ["01", "11"]},
    {"family": ["f7"], "name": ["65"]},
    {"family": ["f7"], "name": ["69", "79"]},
    {"family": ["g0"], "name": ["70", "b0"]},
    {"family": ["g0"], "name": ["71", "81"]},
    {"family": ["g4"], "name": ["11"]},
    {"family": ["g4"], "name": ["14"]},
    {"family": ["g4"], "name": ["71"]},
    {"family": ["g4"], "name": ["73", "83"]},
    {"family": ["g4"], "name": ["74", "84"]},
    {"family": ["h5"], "name": ["e4", "e5", "f4", "f5"], "variant": [""]},
    {"family": ["h5"], "name": ["e4", "e5", "f4", "f5"], "variant": ["q"]},
    {"family": ["h7"], "name": ["25", "35"]},
    {"family": ["h7"], "name": ["45", "55", "47", "57"]},
    {"family": ["h7"], "name": ["a0", "b0", "a3", "b3"], "variant": [""]},
    {"family": ["h7"], "name": ["a0", "b0", "a3", "b3"], "variant": ["q"]},
    {"family": ["h7"], "name": ["r3", "s3"]},
    {"family": ["h7"], "name": ["r7", "s7"]},
    {"family": ["l0"], "name": ["10"]},
    {"family": ["l1"], "name": ["00"]},
    {"family": ["l1"], "name": ["51", "52"], "size": ["6", "8", "b"]},
    {"family": ["l4"], "name": ["51", "71"]},
    {"family": ["l4"], "name": ["32", "42"]},
    {"family": ["l4"], "name": ["76", "86"]},
    {"family": ["l4"], "name": ["r5", "r7", "r9"]},
    {"family": ["l4"], "name": ["s5", "s7", "s9"]},
    {"family": ["l4"], "name": ["p5"]},
    {"family": ["l4"], "name": ["q5"]},
    {"family": ["u3"], "name": ["b5", "c5"], "variant": [""]},
    {"family": ["u3"], "name": ["b5", "c5"], "variant": ["q"]},
    {"family": ["u5"], "name": ["95", "99", "a5", "a9"], "variant": [""]},
    {"family": ["u5"], "name": ["95", "99", "a5", "a9"], "variant": ["q"]},
    {"family": ["u5"], "name": ["f7", "f9", "g7", "g9"], "variant": [""]},
    {"family": ["u5"], "name": ["f7", "f9", "g7", "g9"], "variant": ["q"]},
    {"family": ["wb"], "name": ["30", "50"]},
    {"family": ["wl"], "name": ["33"]},
    {"family": ["wl"], "name": ["54", "55"]},
]


def device_trees(prefixes: list[str]) -> dict[str, DeviceTree]:
    """
    :param prefixes: STM32 device name prefixes, for example, `stm32f4`.
    :return: A mapping of partname to unmerged device tree for every device.
    """
    partnames = set(
        p for prefix in prefixes for p in cubemx.devices_from_prefix(prefix.upper())
    )
    # Expand the temperature placeholder while keeping the order of the full device names
    names = sorted(
        (p[:12] + t + p[13:], p) for p in partnames for t in cubemx.temperature_codes(p)
    )
    devices = {p: cubemx.devices_from_partname(p) for p in sorted(partnames)}
    trees = {}
    for name, partname in names:
        for device in devices[partname]:
            did = device["id"].copy()
            did.set("temperature", name[12])
            trees[did.string] = _device_tree(device, did)
    return trees


def merge_device_trees(trees: list[DeviceTree]) -> list[tuple[str, DeviceTree]]:
    """
    Merges STM32 devices with the same silicon die unless a merge group
    matches. The file names are extended with the size, pin, and variant
    identifiers until they are unique.
    """
    mergeable = defaultdict(list)
    for tree in trees:
        index = group_index(stm_groups, tree.ids[0])
        if index >= 0:
            mergeable[index].append(tree)
        else:
            for child in tree.children:
                if child.name == "attribute-die":
                    mergeable[child["value"]].append(tree)

    def filename(ids, extra=None):
        p = {k: "_".join(v) for k in ids.keys() if len(v := ids.getAttribute(k)) > 0}
        fmt = "stm32{family}-{name}"
        for v in extra or []:
            fmt += f"-{{{v}}}"
        return fmt.format(**p)

    def filename_pre(ids, extra=None):
        index = group_index(stm_groups, ids[0])
        if index != -1:
            extra = list(sorted(set(stm_groups[index].keys()) - {"family", "name"}))
        return filename(ids, extra=extra), ids

    result = []
    filenames_pre = defaultdict(list)
    for group in mergeable.values():
        tree = group[0]
        for other in group[1:]:
            tree.merge(other)
        tree._sortTree()
        result.append(tree)
        name, ids = filename_pre(tree.ids)
        filenames_pre[name].append(ids)

    # Extend the file names until they are unique
    filenames = {}
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

    return [(filenames[frozenset(tree.ids)], tree) for tree in result]


def _device_tree(p, did) -> DeviceTree:
    tree = DeviceTree("device")
    tree.ids.append(did)
    LOGGER.info("Generating Device Tree for '%s'", did.string)

    def driverOrder(e):
        if e.name == "driver":
            if e["name"] == "core":
                # place the core at the very beginning
                return ("aaaaaaa", e.get("type", ""))
            if e["name"] == "dma":
                # place the dma before the gpio
                return ("yyyyyyy", e["type"])
            if e["name"] == "gpio":
                # place the gpio at the very end
                return ("zzzzzzz", e["type"])
            # sort remaining drivers by type and compatible strings
            return (e["name"], e["type"])
        if e.name == "attribute-die":
            return ("0000000", e["value"])
        return ("", "")

    tree.addSortKey(driverOrder)
    tree.addChild("attribute-die").setValue(p["die"])

    core_child = tree.addChild("driver")
    core_child.setAttributes("name", "core")
    if "@" in did.naming_schema:
        core_child.addChild("attribute-type").setValue(p["core"])
        if "revision" in p:
            core_child.addChild("attribute-revision").setValue(p["revision"])
        if "fpu" in p:
            core_child.addChild("attribute-fpu").setValue(p["fpu"])
    else:
        core_child.setAttributes("type", p["core"])
        core_child.setAttributes(["fpu", "revision"], p)
    core_child.addChild("attribute-cmsis-define").setValue(p["define"])
    core_child.addChild("attribute-cmsis-header").setValue(p["cmsis_header"])
    core_child.addSortKey(
        lambda e: (e.name, e["value"]) if e.name.startswith("attribute-") else ("", "")
    )
    _add_memories(p, core_child)
    _add_interrupts(p, core_child)

    modules = {}
    for m, i, _, h, f, pr in p["modules"]:
        if m + h not in modules:
            modules[m + h] = (m, h, f, pr, [i])
        else:
            modules[m + h][4].append(i)

    for name, hardware, features, protocols, instances in modules.values():
        driver = tree.addChild("driver")
        driver.setAttributes("name", name, "type", hardware)
        if name == "gpio":
            _add_gpios(p, did, driver)
            continue

        def driver_sort_key(e):
            if e.name == "feature":
                return (0, 0, e.get("value", "AAA"))
            if e.name == "instance":
                if e["value"].isdigit():
                    return (1, int(e["value"]), "")
                return (1, 0, e["value"])
            return (1e6, 1e6, 1e6)

        driver.addSortKey(driver_sort_key)
        for f in features:
            driver.addChild("feature").setValue(f)
        if any(i != name for i in instances):
            for i in instances:
                driver.addChild("instance").setValue(
                    i[len(name) :].replace("_m", "cortex-m")
                )

        if name == "flash":
            driver.addSortKey(lambda e: int(e.get("vcore-min", 1e6)))
            for mV, freqs in p["flash_latency"].items():
                vddc = driver.addChild("latency")
                vddc.setAttributes("vcore-min", mV)
                vddc.addSortKey(lambda e: (int(e["ws"]), int(e["hclk-max"])))
                for fi, fmax in enumerate(freqs):
                    vddc.addChild("wait-state").setAttributes(
                        "ws", fi, "hclk-max", fmax
                    )

        if name == "rcc":
            driver.addSortKey(lambda e: int(e.get("max-frequency", 1e10)))
            driver.addChild("max-frequency").setValue(p["max_frequency"])

        if name in ["dma", "bdma"]:
            # BDMA1 channel requests are hard-wired to the DFSDM filter channels.
            # The routing is fixed. Thus, no configuration data is available.
            if instances != ["bdma1"]:
                _add_dma(p, driver)
    return tree


def _add_dma(p, driver):
    driver_name = driver["name"]
    naming = p[driver_name + "_naming"]
    driver.addSortKey(lambda e: (int(e.get("instance", 0)), int(e.get("position", 0))))
    for instance, streams in p[driver_name].items():
        inst = driver.addChild((naming[1] if naming[0] is None else naming[0]) + "s")
        if naming[0] is not None or naming[1] == "channel":
            inst.setAttribute("instance", instance)
        inst.addSortKey(lambda e: (e.name, int(e["position"])))
        for stream, channels in streams.items():
            if naming[0] is not None:
                stre = inst.addChild(naming[0])
                stre.setAttribute("position", stream)
                stre.addSortKey(lambda e: int(e["position"]))
            else:
                stre = inst
            for channel, signals in channels.items():
                chan = stre.addChild(naming[1])
                chan.setAttribute("position", channel)
                chan.addSortKey(
                    lambda e: (e["driver"], e.get("instance", ""), e.get("name", ""))
                )
                for signal in signals:
                    sign = chan.addChild(naming[2])
                    sign.setAttributes(["driver", "instance"], signal)
                    if signal["name"]:
                        sign.setAttributes(["name"], signal)
                    sign.addSortKey(lambda e: (e["position"], e["id"]))
                    for remap in signal.get("remap", []):
                        sign.addChild("remap").setAttributes(
                            ["position", "mask", "id"], remap
                        )

    mux_channels = p.get(driver_name + "_mux_channels")
    if mux_channels is not None:
        driver_channels = driver.addChild("mux-channels")
        driver_channels.addSortKey(
            lambda e: (
                int(e.get("position", 0)),
                int(e.get("dma-instance", 0)),
                int(e.get("dma-channel", 0)),
            )
        )
        for channel in mux_channels:
            driver_channels.addChild("mux-channel").setAttributes(
                ["position", "dma-instance", "dma-channel"], channel
            )


def _add_gpios(p, did, gpio_driver):
    if did.family == "f1":
        # Add the remap group tree
        for remap in p["remaps"].values():
            if len(remap["groups"]) == 0:
                continue
            remap_ch = gpio_driver.addChild("remap")
            keys = [k for k in ["driver", "instance"] if remap[k] is not None]
            remap_ch.setAttributes(keys + ["position", "mask"], remap)
            remap_ch.addSortKey(lambda e: int(e["id"]))

            for group, pins in remap["groups"].items():
                group_ch = remap_ch.addChild("group")
                group_ch.setAttributes("id", group)
                group_ch.addSortKey(lambda e: (e["port"], int(e["pin"]), e["name"]))
                for pin in pins:
                    group_ch.addChild("signal").setAttributes(
                        ["port", "pin", "name"], pin
                    )

    package = gpio_driver.addChild("package")
    package.setAttributes("name", p["package"])

    def sort_pinout(e):
        alphas = "".join(filter(str.isalpha, e["position"]))
        digits = "".join(filter(str.isdigit, e["position"]))
        return (alphas, int(digits), e.get("variant", ""))

    package.addSortKey(sort_pinout)
    for pin in p["pinout"]:
        pinc = package.addChild("pin")
        pinc.setAttributes(["position", "name"], pin)
        if "I/O" not in pin["type"]:
            pinc.setAttributes("type", pin["type"].lower())
        pinc.setAttributes(["variant"], pin)

    def sort_gpios(e):
        if "package" in e.name:
            return (1000, e["name"], 0, "", 0)
        elif "driver" in e:
            return (int(e["position"]), e["driver"], int(e.get("instance", 0)), "", 0)
        return (100, "", 0, e["port"], int(e["pin"]))

    gpio_driver.addSortKey(sort_gpios)

    for port, pin, signals in p["gpios"]:
        pin_driver = gpio_driver.addChild("gpio")
        pin_driver.setAttributes("port", port, "pin", pin)
        pin_driver.addSortKey(
            lambda e: (
                int(e.get("af", -1)),
                e.get("driver", ""),
                e.get("instance", ""),
                e["name"],
            )
        )
        for s in signals:
            afid, driver, instance, name = (
                s["af"],
                s["driver"],
                s["instance"],
                s["name"],
            )
            # EXTI lines are available on all pins and not listed as signals
            if "exti" in name:
                continue
            if driver == "spdifrx" and instance == "1":
                # Only one peripheral ever exists, but some H7 have instance "1"
                # Naming in manuals and headers is always without "1"
                instance = None
            af = pin_driver.addChild("signal")
            if afid == "":
                LOGGER.error("afid is not set: %s", s)
            if afid:
                af.setAttributes("af", afid)
            if driver:
                af.setAttributes("driver", driver)
            if instance:
                af.setAttributes("instance", instance)
            af.setAttributes("name", name)


def _add_memories(p, node):
    for section in p["memories"]:
        memory = node.addChild("memory")
        memory.setAttributes(["name", "access"], section)
        memory.setAttributes("start", f"0x{section['start']:02X}")
        memory.setAttributes(["size", "alias"], section)
    # sort the node children by start address and size
    node.addSortKey(
        lambda e: (int(e["start"], 16), int(e["size"]))
        if e.name == "memory"
        else (-1, -1)
    )


def _add_interrupts(p, node):
    for vector in p["interrupts"]:
        if vector["position"] >= 0:
            node.addChild("vector").setAttributes(["position", "name"], vector)
    # sort the node children by vector number and name
    node.addSortKey(
        lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, "")
    )
