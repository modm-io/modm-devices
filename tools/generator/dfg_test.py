# Copyright 2026, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

import io
import unittest
import tempfile
from pathlib import Path

from modm_data.kg import DeviceIdentifier
from dfg import (
    MultiDeviceIdentifier,
    DeviceTree,
    merge,
    group_index,
    format_device_file,
)
from dfg import generate_device_files, VerificationError
from dfg.merger import filename_from_ids
from dfg.generator import _canonical, _parser


def did(name, size):
    i = DeviceIdentifier("{platform}{family}{name}{size}")
    i.set("platform", "stm32")
    i.set("family", "f4")
    i.set("name", name)
    i.set("size", size)
    return i


def tree(name, size, instances):
    t = DeviceTree("device")
    t.ids.append(did(name, size))
    core = t.addChild("driver")
    core.setAttributes("name", "core", "type", "cortex-m4")
    core.addChild("memory").setAttributes(
        "name", "flash", "size", {"e": 512, "g": 1024}[size]
    )
    uart = t.addChild("driver")
    uart.setAttributes("name", "uart", "type", "stm32")
    uart.addSortKey(lambda e: int(e["value"]))
    for instance in instances:
        uart.addChild("instance").setValue(instance)
    return t


class MultiDeviceIdentifierTest(unittest.TestCase):
    def test_attributes(self):
        ids = MultiDeviceIdentifier()
        for name, size in [("07", "e"), ("07", "g"), ("05", "g")]:
            ids.append(did(name, size))
        self.assertEqual(ids.getAttribute("name"), ["05", "07"])
        self.assertEqual(ids.getAttribute("size"), ["e", "g"])
        self.assertEqual(ids.string, "stm32f4[05|07][e|g]")
        self.assertEqual(len(ids.product()), 4)

    def test_minimal_subtract_set(self):
        complete = MultiDeviceIdentifier.from_list(
            [did(n, s) for n in ["05", "07"] for s in ["e", "g"]]
        )
        subset = complete.filter(lambda d: d.size == "g")
        diffs = subset.minimal_subtract_set(complete, complete)
        self.assertEqual([d.string for d in diffs], ["g"])
        self.assertEqual(diffs[0].keys(), ["size"])


class MergerTest(unittest.TestCase):
    def test_group_index(self):
        groups = [{"family": ["f4"], "name": ["05"]}, {"family": ["f4"]}]
        self.assertEqual(group_index(groups, did("05", "e")), 0)
        self.assertEqual(group_index(groups, did("07", "e")), 1)
        self.assertEqual(group_index(groups[:1], did("07", "e")), -1)

    def test_filename(self):
        ids = MultiDeviceIdentifier.from_list([did("07", "e"), did("05", "g")])
        self.assertEqual(
            filename_from_ids(ids, "stm32{family}-{name}"), "stm32f4-05_07"
        )

    def test_merge_roundtrip(self):
        trees = {
            "stm32f405e": tree("05", "e", ["1", "2"]),
            "stm32f407e": tree("07", "e", ["1", "2", "3"]),
            "stm32f407g": tree("07", "g", ["1", "2", "3"]),
        }
        single = {name: format_device_file(t.copy()) for name, t in trees.items()}
        merged = merge([{"family": ["f4"]}], trees.values())
        self.assertEqual(len(merged), 1)

        parser = _parser()
        devices = parser.parse(io.BytesIO(format_device_file(merged[0]))).get_devices()
        self.assertEqual(sorted(d.partname for d in devices), sorted(trees))
        for device in devices:
            expected = parser.parse(io.BytesIO(single[device.partname])).get_devices()[
                0
            ]
            self.assertEqual(
                _canonical(device.properties, False),
                _canonical(expected.properties, False),
            )

    def test_generate_verifies(self):
        trees = {
            "stm32f405e": tree("05", "e", ["1"]),
            "stm32f407e": tree("07", "e", ["1", "2"]),
        }
        with tempfile.TemporaryDirectory() as folder:
            paths = generate_device_files(
                trees,
                lambda ts: [("stm32f4", t) for t in merge([{"family": ["f4"]}], ts)],
                Path(folder),
            )
            self.assertEqual([p.name for p in paths], ["stm32f4.xml"])

    def test_generate_detects_errors(self):
        trees = {
            "stm32f405e": tree("05", "e", ["1"]),
            "stm32f407e": tree("07", "e", ["1", "2"]),
        }

        def broken_merger(ts):
            # Drop a device, which must be detected
            return [("stm32f4", ts[0])]

        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaises(VerificationError),
        ):
            generate_device_files(trees, broken_merger, Path(folder))

    def test_canonical(self):
        self.assertEqual(
            _canonical([{"a": ["2", "1"]}, "x", "x"], True), ["x", {"a": ["1", "2"]}]
        )
        self.assertEqual(_canonical(["x", "x"], False), ["x", "x"])


if __name__ == "__main__":
    unittest.main()
