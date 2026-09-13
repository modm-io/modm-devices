# Copyright 2013, Niklas Hauser
# Copyright 2016, Fabian Greif
# Copyright 2022, Christopher Durand
# SPDX-License-Identifier: MPL-2.0

import re
import logging

from modm_data.atdf import sam
from .tree import DeviceTree
from .merger import merge, filename_from_ids

LOGGER = logging.getLogger(__name__)
PLATFORM = "sam"

sam_groups = [
    {"series": ["d10", "d11"]},
    {"series": ["d09"]},
    {"series": ["da1"]},
    {"series": ["d20"]},
    {"series": ["d21"]},
    {"series": ["d51", "e51", "e53", "e54"]},
    {"series": ["l21"]},
    {"series": ["l22"]},
    {"series": ["g51", "g53", "g54"]},
    {"series": ["g55"]},
    {"series": ["e70", "s70", "v70", "v71"]},
]


def device_trees(prefixes: list[str]) -> dict[str, DeviceTree]:
    """
    :param prefixes: SAM device prefixes, for example, `samd21`.
    :return: A mapping of partname to unmerged device tree for every device.
    """
    trees = {}
    for prefix in prefixes:
        for path in sam.device_files(prefix):
            for ordercode in sam.devices_from_file(path):
                p = sam.device_from_ordercode(path, ordercode)
                trees[p["id"].string] = _device_tree(p)
    return trees


def merge_device_trees(trees: list[DeviceTree]) -> list[tuple[str, DeviceTree]]:
    """Merges SAM devices by merge groups and names the files by their series."""
    merged = merge(sam_groups, trees)
    return [
        (
            filename_from_ids(
                t.ids, "{platform}{series}", empty="n", sort_keys=("type", "pin")
            ),
            t,
        )
        for t in merged
    ]


def _device_tree(p) -> DeviceTree:
    tree = DeviceTree("device")
    tree.ids.append(p["id"])

    # There are two groups of devices with common peripherals:
    # - SAM x7x,G5x
    # - SAM D09,D1x,D2x,L2x,D51,E5x
    compatible = "samg" if p["id"].string.startswith("samg5") else "sam"

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
    core_child.setAttributes(["fpu", "revision"], p)
    core_child.addSortKey(
        lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, "")
    )
    core_child.addSortKey(
        lambda e: (e["name"], int(e["size"])) if e.name == "memory" else ("", -1)
    )
    core_child.addSortKey(
        lambda e: (e.name, e["value"]) if e.name.startswith("attribute-") else ("", "")
    )

    for section in p["memories"]:
        core_child.addChild("memory").setAttributes(
            ["name", "access", "start", "size"], section
        )
    # sort the node children by start address and size
    core_child.addSortKey(
        lambda e: (int(e["start"], 16), int(e["size"]))
        if e.name == "memory"
        else (-1, -1)
    )

    for vector in p["interrupts"]:
        if int(vector["position"]) < 0:
            continue
        core_child.addChild("vector").setAttributes(["position", "name"], vector)

    modules = {}
    for m, i in p["modules"]:
        # filter out non-peripherals: fuses, micro-trace buffer
        if m in ["fuses", "mtb", "systemcontrol", "systick", "hmatrixb", "hmatrix"]:
            continue
        modules.setdefault(m, []).append(i)

    # add all other modules
    instance_pattern = re.compile(r"^(?P<per>([a-z0-9]*[a-z]+))(?P<instance>([0-9]+))$")
    for name, instances in modules.items():
        driver = tree.addChild("driver")
        dtype = name
        driver.setAttributes("name", dtype, "type", compatible)
        # Add all instances to this driver
        if any(i != dtype for i in instances):
            driver.addSortKey(lambda e: e["value"])
            for i in instances:
                driver.addChild("instance").setValue(i[len(dtype) :])
        if name == "gclk":
            driver.addSortKey(
                lambda e: (
                    e.name,
                    int(e["value"]),
                    e.get("peripheral", ""),
                    e.get("instance", ""),
                    e.get("name", ""),
                )
            )
            for instance, instance_clocks in p["gclk_data"]["clocks"].items():
                for clock_name, clock_id in instance_clocks:
                    clock = driver.addChild("clock")
                    if m := instance_pattern.match(instance):
                        clock.setAttributes(
                            "peripheral",
                            m.group("per"),
                            "instance",
                            m.group("instance"),
                        )
                    else:
                        clock.setAttributes("peripheral", instance)
                    if clock_name is not None:
                        clock.setAttribute("name", clock_name)
                    clock.setAttribute("value", clock_id)
            for source_name, source_id in p["gclk_data"]["sources"].items():
                driver.addChild("source").setAttributes(
                    "name", source_name, "value", source_id
                )
            driver.addChild("generators").setAttributes(
                "value", str(p["gclk_data"]["generator_count"])
            )
        # Add request data to DMA module
        # Skip D09 devices, information is missing in raw data.
        elif name in ("dmac", "xdmac", "pdc") and p["id"].series != "d09":
            driver.addSortKey(
                lambda e: (
                    int(e["id"]),
                    e["peripheral"],
                    e.get("instance", ""),
                    e["signal"],
                )
            )
            for instance, request_list in p["dma_requests"].items():
                for signal, request_id in request_list:
                    req = driver.addChild("request")
                    if m := instance_pattern.match(instance):
                        req.setAttributes(
                            "peripheral",
                            m.group("per"),
                            "instance",
                            m.group("instance"),
                        )
                    else:
                        req.setAttributes("peripheral", instance)
                    req.setAttributes("signal", signal, "id", request_id)

    # GPIO driver
    gpio_driver = tree.addChild("driver")
    gpio_driver.setAttributes("name", "gpio", "type", compatible)
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
            pin_signal = {"driver": driver, "function": s["function"]}
            if "index" in s:
                pin_signal["index"] = s["index"]
            if instance != driver:
                pin_signal["instance"] = instance.replace(driver, "")
            if name != driver and name != "int":
                pin_signal["name"] = name
            elif "index" in s:
                pin_signal["name"] = s["index"]
            if "name" not in pin_signal:
                LOGGER.error("%s has no name!", s)
                continue
            pin_driver.addChild("signal").setAttributes(
                ["driver", "instance", "name", "function", "index"], pin_signal
            )

    return tree
