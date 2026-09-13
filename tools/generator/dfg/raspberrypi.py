# Copyright 2022, Andrey Kunitsyn
# SPDX-License-Identifier: MPL-2.0

import logging

from modm_data import picosdk
from .tree import DeviceTree
from .merger import merge, filename_from_ids

LOGGER = logging.getLogger(__name__)
PLATFORM = "rp"

rp_groups = [{"family": ["20"]}]


def device_trees(prefixes: list[str]) -> dict[str, DeviceTree]:
    """
    :param prefixes: RP device prefixes, for example, `rp2040`.
    :return: A mapping of partname to unmerged device tree for every device.
    """
    trees = {}
    for prefix in prefixes:
        for path in picosdk.device_files(prefix):
            p = picosdk.device_from_file(path)
            trees[p["id"].string] = _device_tree(p)
    return trees


def merge_device_trees(trees: list[DeviceTree]) -> list[tuple[str, DeviceTree]]:
    """Merges RP devices by merge groups and names the files by their identifiers."""
    return [
        (filename_from_ids(t.ids, "{platform}{family}{ram}{flash}"), t)
        for t in merge(rp_groups, trees)
    ]


def _device_tree(p) -> DeviceTree:
    tree = DeviceTree("device")
    tree.ids.append(p["id"])

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
    core_child.addSortKey(
        lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, "")
    )

    modules = {}
    for m, i in p["modules"]:
        # gpio, clock, usb, xip, and adc subsystems are handled separately
        if m in [
            "pads_bank",
            "pads_qspi",
            "pll_usb",
            "pll_sys",
            "xosc",
            "usbctrl_regs",
            "usbctrl_dpram",
        ]:
            continue
        if m in ["xip_ctrl", "adc"]:
            continue
        modules.setdefault(m, []).append(i)

    compatible = p["id"]["platform"] + p["id"]["family"]
    for name, instances in modules.items():
        driver = tree.addChild("driver")
        driver.setAttributes("name", name, "type", compatible)
        # Add all instances to this driver
        if any(i != name for i in instances):
            driver.addSortKey(lambda e: e["value"])
            for i in instances:
                driver.addChild("instance").setValue(i[len(name) :])

    # GPIO driver
    gpio_driver = tree.addChild("driver")
    gpio_driver.setAttributes("name", "gpio", "type", compatible)
    gpio_driver.addSortKey(lambda e: (e["port"], int(e["pin"])))
    for pin in p["gpios"]:
        pin_driver = gpio_driver.addChild("gpio")
        pin_driver.setAttributes(
            "port", pin["bank"], "pin", str(pin["idx"]), "name", pin["name"]
        )
        for s in pin["signals"]:
            signal = pin_driver.addChild("signal")
            signal.setAttributes(
                "driver", s["driver"], "name", s["name"], "af", s["af"]
            )
            if "instance" in s:
                signal.setAttribute("instance", s["instance"])
        pin_driver.addSortKey(lambda e: (e["af"], e["name"]))

    # ADC driver
    adc_driver = tree.addChild("driver")
    adc_driver.setAttributes("name", "adc", "type", compatible)
    for ch in p["adc_channels"]:
        ch_driver = adc_driver.addChild("channel")
        ch_driver.setAttribute("id", ch["id"])
        ch_driver.setAttribute("name", ch["name"])
        ch_driver.addSortKey(lambda e: (-1, e["id"]))

    # DMA driver
    dma_driver = tree.addChild("driver")
    dma_driver.setAttributes("name", "dma", "type", compatible)
    for ch in p["dma_channels"]:
        ch_driver = dma_driver.addChild("channel")
        ch_driver.setAttributes("name", ch["name"])
        ch_driver.addSortKey(lambda e: (-1, e["name"]))

    # Clocks driver
    clocks_driver = tree.addChild("driver")
    clocks_driver.setAttributes("name", "clocks", "type", compatible)
    for clk in p["clocks"]:
        clk_driver = clocks_driver.addChild("clock")
        clk_driver.setAttributes(
            "name",
            clk["name"],
            "glitchless",
            "true" if clk["glitchless"] else "false",
            "idx",
            clk["idx"],
        )
        for src in clk["sources"]:
            clk_driver.addChild("source").setAttributes(
                "name", src["name"], "src", src["src"], "aux", src["aux"]
            )

    return tree
