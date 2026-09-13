# Copyright 2013, Niklas Hauser
# Copyright 2016, Fabian Greif
# SPDX-License-Identifier: MPL-2.0

import logging

from modm_data.atdf import avr
from .tree import DeviceTree
from .merger import merge, group_index, filename_from_ids

LOGGER = logging.getLogger(__name__)
PLATFORM = "avr"

avr_groups = [
    {"family": ["90"], "name": ["1", "2", "216"], "type": ["pwm"]},
    {"family": ["90"], "name": ["3", "316"], "type": ["pwm"]},
    {"family": ["90"], "name": ["32", "64", "128"], "type": ["can"]},
    {"family": ["90"], "name": ["82", "162"], "type": ["usb"]},
    {"family": ["90"], "name": ["81", "161"], "type": ["pwm"]},
    {"family": ["90"], "name": ["646", "647", "1286", "1287"], "type": ["usb"]},
    {"family": ["tiny"], "name": ["4", "5", "9", "10"]},
    {"family": ["tiny"], "name": ["11", "12", "13", "15"]},
    {"family": ["tiny"], "name": ["20"]},
    {"family": ["tiny"], "name": ["24", "44", "84"]},
    {"family": ["tiny"], "name": ["25", "45", "85"]},
    {"family": ["tiny"], "name": ["26"]},
    {"family": ["tiny"], "name": ["40"]},
    {"family": ["tiny"], "name": ["43"]},
    {"family": ["tiny"], "name": ["48", "88"]},
    {"family": ["tiny"], "name": ["80", "840"]},
    {"family": ["tiny"], "name": ["87", "167"]},
    {"family": ["tiny"], "name": ["102", "104"]},
    {"family": ["tiny"], "name": ["202", "402", "802"]},
    {
        "family": ["tiny"],
        "name": ["204", "404", "406", "804", "806", "807", "1604", "1606", "1607"],
    },
    {"family": ["tiny"], "name": ["212", "412"]},
    {"family": ["tiny"], "name": ["261", "461", "861"]},
    {"family": ["tiny"], "name": ["441", "841"]},
    {"family": ["tiny"], "name": ["416", "816", "1616", "3216"]},
    {"family": ["tiny"], "name": ["417", "817", "1617", "3217"]},
    {"family": ["tiny"], "name": ["214", "414", "814", "1614", "3214"]},
    {"family": ["tiny"], "name": ["828"]},
    {"family": ["tiny"], "name": ["1634"]},
    {"family": ["tiny"], "name": ["2313", "4313"]},
    {"family": ["mega"], "name": ["8", "16", "32"], "type": ["u2"]},
    {"family": ["mega"], "name": ["8", "16", "32"], "type": ["", "a", "l"]},
    {"family": ["mega"], "name": ["8", "16"], "type": ["hva"]},
    {"family": ["mega"], "name": ["16", "32"], "type": ["u4", "u4rc"]},
    {"family": ["mega"], "name": ["16", "32"], "type": ["hvb", "hvbrevb"]},
    {"family": ["mega"], "name": ["16", "32", "64"], "type": ["hve2"]},
    {
        "family": ["mega"],
        "name": ["48", "88", "168", "328"],
        "type": ["", "a", "p", "pa", "v", "pv"],
    },
    {"family": ["mega"], "name": ["48", "88", "168", "328"], "type": ["pb"]},
    {"family": ["mega"], "name": ["64", "128"], "type": ["", "a", "l"]},
    {"family": ["mega"], "name": ["64", "128", "256"], "type": ["rfa1", "rfr2"]},
    {
        "family": ["mega"],
        "name": ["16", "32", "64", "128", "256"],
        "type": ["m1", "c1"],
    },
    {"family": ["mega"], "name": ["162"]},
    {
        "family": ["mega"],
        "name": ["164", "324", "644"],
        "type": ["", "a", "p", "v", "pa", "pv"],
    },
    {"family": ["mega"], "name": ["1284"], "type": ["", "a", "p", "pa"]},
    {"family": ["mega"], "name": ["164", "324", "644", "1284"], "type": ["pb"]},
    {"family": ["mega"], "name": ["165", "325", "645"]},
    {"family": ["mega"], "name": ["169", "329", "649"]},
    {"family": ["mega"], "name": ["406"]},
    {"family": ["mega"], "name": ["640", "1280", "2560"]},
    {"family": ["mega"], "name": ["1281", "2561"]},
    {"family": ["mega"], "name": ["644", "1284", "2564"], "type": ["rfr2"]},
    {"family": ["mega"], "name": ["3208", "3209", "4808", "4809"]},
    {"family": ["mega"], "name": ["3250", "6450"]},
    {"family": ["mega"], "name": ["3290", "6490"]},
    {"family": ["mega"], "name": ["8515"]},
    {"family": ["mega"], "name": ["8535"]},
    {"family": ["xmega"], "type": ["a1"]},
    {"family": ["xmega"], "type": ["a3"], "pin": ["", "b"]},
    {"family": ["xmega"], "type": ["a3"], "pin": ["bu", "u"]},
    {"family": ["xmega"], "type": ["a4"]},
    {"family": ["xmega"], "type": ["b1"]},
    {"family": ["xmega"], "type": ["b3"]},
    {"family": ["xmega"], "type": ["c3"]},
    {"family": ["xmega"], "type": ["c4"]},
    {"family": ["xmega"], "type": ["d3"]},
    {"family": ["xmega"], "type": ["d4"]},
    {"family": ["xmega"], "type": ["e5"]},
]


def device_trees(prefixes: list[str]) -> dict[str, DeviceTree]:
    """
    :param prefixes: AVR device prefixes, for example, `atmega`.
    :return: A mapping of partname to unmerged device tree for every device.
    """
    trees = {}
    for prefix in prefixes:
        for path in avr.device_files(prefix):
            for ordercode in avr.devices_from_file(path):
                if (p := avr.device_from_ordercode(path, ordercode)) is not None:
                    trees[p["id"].string] = _device_tree(p)
    return trees


def merge_device_trees(trees: list[DeviceTree]) -> list[tuple[str, DeviceTree]]:
    """Merges AVR devices by merge groups and names the files by the group keys."""
    return [(_filename(tree.ids), tree) for tree in merge(avr_groups, trees)]


def _filename(ids) -> str:
    fmt = "at{family}"
    index = group_index(avr_groups, ids[0])
    if index == -1:
        fmt += "-{name}-{type}"
    else:
        keys = avr_groups[index].keys()
        for key in ["name", "type", "pin"]:
            if key in keys:
                fmt += f"-{{{key}}}"
    return filename_from_ids(ids, fmt, empty="n", sort_keys=("type", "pin"))


def _device_tree(p) -> DeviceTree:
    tree = DeviceTree("device")
    tree.ids.append(p["id"])
    LOGGER.info("Generating Device Tree for '%s'", p["id"].string)

    def topLevelOrder(e):
        order = [
            "attribute-flash",
            "attribute-ram",
            "attribute-eeprom",
            "attribute-core",
            "attribute-mcu",
            "header",
        ]
        order += ["attribute-define"]
        if e.name in order:
            if e.name in ["attribute-flash", "attribute-eeprom", "attribute-ram"]:
                return (order.index(e.name), int(e["value"]))
            return (order.index(e.name), e["value"])
        return (len(order), -1)

    tree.addSortKey(topLevelOrder)
    tree.addChild("attribute-mcu").setValue(p["mcu"])

    def driverOrder(e):
        if e.name == "driver":
            if e["name"] == "core":
                # place the core at the very beginning
                return ("aaaaaaa", e["type"])
            if e["name"] == "gpio":
                # place the gpio at the very end
                return ("zzzzzzz", e["type"])
            # sort remaining drivers by type and compatible strings
            return (e["name"], e["type"])
        return ("", "")

    tree.addSortKey(driverOrder)

    # Core
    core_child = tree.addChild("driver")
    core_child.setAttributes("name", "core", "type", p["core"])
    core_child.addSortKey(
        lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, "")
    )
    core_child.addSortKey(
        lambda e: (e["name"], int(e["size"])) if e.name == "memory" else ("", -1)
    )
    core_child.addSortKey(lambda e: int(e["value"]) if e.name == "fcpu" else 1e9)
    for memory in ["flash", "ram", "eeprom"]:
        if memory not in p:
            continue
        memory_section = core_child.addChild("memory")
        memory_section.setAttribute("name", memory)
        memory_section.setAttribute("size", p[memory])
    core_child.addChild("fcpu").setValue(p["max_fcpu"])

    # Clock
    tree.addChild("driver").setAttributes("name", "clock", "type", "avr")

    modules = {}
    for m, i in p["modules"]:
        # filter out non-peripherals
        if m in [
            "cpu",
            "jtag",
            "exint",
            "fuse",
            "gpio",
            "lockbit",
            "boot_load",
            "clkctrl",
            "cpuint",
        ]:
            continue
        modules.setdefault(m, []).append(i)

    # add all other modules
    for name, instances in modules.items():
        driver = tree.addChild("driver")
        dtype = name
        compatible = "avr"
        if name.startswith("tc"):
            dtype = "tc"
            compatible = name

        driver.setAttributes("name", dtype, "type", compatible)
        # Add all instances to this driver
        if any(i != dtype for i in instances):
            driver.addSortKey(lambda e: e["value"])
            for i in instances:
                driver.addChild("instance").setValue(i[len(dtype) :])

    # GPIO driver
    gpio_driver = tree.addChild("driver")
    gpio_driver.setAttributes("name", "gpio", "type", "avr")
    gpio_driver.addSortKey(lambda e: (e["port"], int(e["pin"])))
    for port, pin in p["gpios"]:
        pin_driver = gpio_driver.addChild("gpio")
        pin_driver.setAttributes("port", port.upper(), "pin", pin)
        pin_driver.addSortKey(
            lambda e: (
                e["driver"],
                e["instance"] if e["instance"] is not None else "",
                e["name"] if e["name"] is not None else "",
            )
        )
        # add all signals
        for s in [s for s in p["signals"] if s["pad"] == ("p" + port + pin)]:
            driver, instance, name = s["module"], s["instance"], s["group"]
            if driver.startswith("tc"):
                driver = "tc"
            if driver == "cpu":
                driver = "core"
                instance = "core"
            pin_signal = {"driver": driver}
            if instance != driver:
                pin_signal["instance"] = instance.replace(driver, "")
            if name != driver and name != "int":
                if "index" in s:
                    name += s["index"]
                pin_signal["name"] = name
            elif "index" in s:
                pin_signal["name"] = s["index"]
            if "name" not in pin_signal:
                LOGGER.error("%s has no name!", s)
                continue
            pin_driver.addChild("signal").setAttributes(
                ["driver", "instance", "name"], pin_signal
            )

    return tree
