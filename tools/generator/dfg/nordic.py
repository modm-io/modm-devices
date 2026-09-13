# Copyright 2020, Hannes Ellinger
# SPDX-License-Identifier: MPL-2.0

import re
import logging

from modm_data import nrfx
from modm_data.nrfx.pinout import package_code_map
from .tree import DeviceTree
from .merger import merge, filename_from_ids

LOGGER = logging.getLogger(__name__)
PLATFORM = "nrf"

nrf_groups = [
    {"family": ["51"], "series": ["422", "801", "802", "822", "824"]},
    {"family": ["52"], "series": ["805", "810", "811"]},
    {"family": ["52"], "series": ["832", "833"]},
    {"family": ["52"], "series": ["820", "840"]},
    {"family": ["53"], "series": ["40"]},
]


def device_trees(prefixes: list[str]) -> dict[str, DeviceTree]:
    """
    :param prefixes: NRF device prefixes, for example, `nrf52`.
    :return: A mapping of device identifier string to unmerged device tree for
             every device, where each tree contains all package variants.
    """
    trees = {}
    for prefix in prefixes:
        for path in nrfx.device_files(prefix):
            tree = _device_tree(nrfx.device_from_file(path))
            trees[tree.ids.string] = tree
    return trees


def merge_device_trees(trees: list[DeviceTree]) -> list[tuple[str, DeviceTree]]:
    """Merges NRF devices by merge groups and names the files by their identifiers."""
    return [
        (filename_from_ids(t.ids, "{platform}{family}{series}"), t)
        for t in merge(nrf_groups, trees)
    ]


def _expanded_device_ids(did, pin_packages):
    package_codes = []
    for package in pin_packages:
        for package_code in package.get("codes", []):
            if package_code not in package_codes:
                package_codes.append(package_code)

    if not package_codes:
        for codes in package_code_map.get(f"nrf{did.family}{did.series}", {}).values():
            for package_code in codes:
                if package_code not in package_codes:
                    package_codes.append(package_code)

    if not package_codes:
        return [did]

    ids = []
    for package_code in package_codes:
        pdid = did.copy()
        pdid.set("package", package_code)
        ids.append(pdid)
    return ids


def _resolve_pin_special_signals(pin_specials, signals_per_driver):
    resolved = {}
    consumed_driver_signals = set()

    for pin_key, tags in pin_specials.items():
        pin_signals = []
        seen = set()
        for tag in tags:
            if tag in ("spim4", "qspi", "trace"):
                continue

            entries = []
            if tag.startswith("spim4_"):
                entries.append(
                    {"driver": "spim", "instance": "4", "name": tag.split("_", 1)[1]}
                )
            elif tag.startswith("qspi_"):
                entries.append({"driver": "qspi", "name": tag.split("_", 1)[1]})
            elif tag == "traceclk":
                entries.append({"driver": "trace", "name": "clk"})
            elif tag.startswith("tracedata"):
                entries.append(
                    {"driver": "trace", "name": tag.replace("tracedata", "data", 1)}
                )
            elif tag == "swo":
                entries.append({"driver": "trace", "name": "swo"})
            elif tag in ("twi", "twim", "twis"):
                for driver in ("twim", "twis", "twi"):
                    if driver not in signals_per_driver:
                        continue
                    for signal_name in ("scl", "sda"):
                        if signal_name in signals_per_driver[driver]:
                            entries.append({"driver": driver, "name": signal_name})
            elif re.fullmatch(r"ain\d+", tag):
                for driver, names in signals_per_driver.items():
                    if tag in names:
                        entries.append({"driver": driver, "name": tag})
                        consumed_driver_signals.add((driver, tag))
            else:
                entries.append({"driver": "special", "name": tag})

            for entry in entries:
                key = (
                    entry.get("driver"),
                    entry.get("instance", ""),
                    entry.get("name"),
                )
                if key not in seen:
                    seen.add(key)
                    pin_signals.append(entry)

        if pin_signals:
            resolved[pin_key] = pin_signals

    return resolved, consumed_driver_signals


def _device_tree(p) -> DeviceTree:
    tree = DeviceTree("device")
    for did in _expanded_device_ids(p["id"], p.get("pin_packages", [])):
        tree.ids.append(did)

    def driverOrder(e):
        if e.name == "driver":
            if e["name"] == "core":
                # place the core at the very beginning
                return ("aaaaaaa", e["type"] + e.get("fpu", ""))
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
        if m in [
            "fuses",
            "mtb",
            "systemcontrol",
            "systick",
            "hmatrixb",
            "hmatrix",
            "approtect",
        ]:
            continue
        modules.setdefault(m, []).append(i)

    # represent peripheral pin capabilities on the peripheral driver itself
    signals_per_driver = {}
    if p["id"]["family"] in ("51", "52", "53"):
        for signal in p["signals"]:
            signals_per_driver.setdefault(signal["driver"], set()).add(
                signal["name"] + signal.get("index", "")
            )
        for driver, names in p.get("fixed_signals", {}).items():
            signals_per_driver.setdefault(driver, set()).update(names)

    resolved_pin_specials, consumed_driver_signals = _resolve_pin_special_signals(
        p.get("pin_specials", {}), signals_per_driver
    )
    for driver_name, signal_name in consumed_driver_signals:
        if driver_name in signals_per_driver:
            signals_per_driver[driver_name].discard(signal_name)

    compatible = p["id"]["platform"] + p["id"]["family"]
    for name, instances in modules.items():
        driver = tree.addChild("driver")
        driver.setAttributes("name", name, "type", compatible)
        # Add all instances to this driver
        if any(i != name for i in instances):
            driver.addSortKey(lambda e: e["value"] if e.name == "instance" else "")
            for i in instances:
                driver.addChild("instance").setValue(i[len(name) :])

        if name in signals_per_driver:
            driver.addSortKey(
                lambda e: (e.get("name", "") or "") if e.name == "signal" else ""
            )
            for signal_name in sorted(signals_per_driver[name]):
                driver.addChild("signal").setAttribute("name", signal_name)

    # GPIO driver
    gpio_driver = tree.addChild("driver")
    gpio_driver.setAttributes("name", "gpio", "type", compatible)

    if p["id"]["family"] not in ("51", "52", "53"):
        for s in p["signals"]:
            driver, instance, name = s["driver"], s["instance"], s["name"]
            gpio_signal = {"driver": driver}
            if instance != driver:
                gpio_signal["instance"] = instance.replace(driver, "")
            if name != driver and name != "int":
                if "index" in s:
                    name += s["index"]
                gpio_signal["name"] = name
            elif "index" in s:
                gpio_signal["name"] = s["index"]
            if "name" not in gpio_signal:
                LOGGER.error("%s has no name!", s)
                continue
            af = gpio_driver.addChild("signal")
            af.setAttributes(["driver", "instance", "name"], gpio_signal)
            af.addSortKey(
                lambda e: (e["driver"], int(e.get("instance", "-1")), e.get("name", ""))
            )

    # add all GPIOs
    gpio_nodes = {}
    for port, pin in p["gpios"]:
        pin_driver = gpio_driver.addChild("gpio")
        pin_driver.setAttributes("port", port, "pin", pin)
        gpio_nodes[f"{port}.{pin}"] = pin_driver

    for pin_key, signals in resolved_pin_specials.items():
        if (gpio_node := gpio_nodes.get(pin_key)) is None:
            continue
        for signal in signals:
            gpio_node.addChild("signal").setAttributes(
                ["driver", "instance", "name"], signal
            )

    for package in p.get("pin_packages", []):
        package_node = gpio_driver.addChild("package")
        if package.get("codes"):
            package_node.ids = tree.ids.filter(
                lambda did: did["package"] in package["codes"]
            )
        package_node.setAttribute("name", package["name"])
        for package_pin in package["pins"]:
            package_node.addChild("pin").setAttributes(
                ["position", "name", "type"], package_pin
            )

    return tree
