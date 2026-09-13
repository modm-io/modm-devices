# Copyright 2016, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

import io
import json
import logging
from pathlib import Path

from .writer import format_device_file

LOGGER = logging.getLogger(__name__)


def _parser():
    # Import lazily, since importing the parser modifies the XML catalog environment
    from modm_devices.parser import DeviceParser

    return DeviceParser()


def _canonical(obj, unique: bool):
    # Lists are compared as (multi)sets, since the merged order is not preserved
    if isinstance(obj, dict):
        return {k: _canonical(v, unique) for k, v in obj.items()}
    if isinstance(obj, list):
        items = {} if unique else []
        for v in obj:
            v = _canonical(v, unique)
            key = json.dumps(v, sort_keys=True)
            if unique:
                items[key] = v
            else:
                items.append((key, v))
        return [
            v
            for _, v in sorted(items.items() if unique else items, key=lambda kv: kv[0])
        ]
    return obj


class VerificationError(Exception):
    pass


def verify_device_file(path: Path, originals: dict) -> tuple[list[str], list[str]]:
    """
    Checks that the device file contains the same properties for every device
    as the unmerged device tree of that device. Duplicate list items are ignored,
    since overlapping device selectors in the merged file duplicate items.

    :param path: Path to the merged device file.
    :param originals: Mapping of device partname to the unmerged device tree containing it.
    :return: The partnames of all devices contained in the device file, and the
             partnames of devices with duplicated items.
    """
    parser = _parser()
    partnames = []
    duplicates = []
    for device in parser.parse(str(path)).get_devices():
        partnames.append(device.partname)
        if (original := originals.get(device.partname)) is None:
            raise VerificationError(
                f"{path.name}: Device '{device.partname}' was not generated!"
            )
        single = parser.parse(io.BytesIO(format_device_file(original))).get_devices()
        single = [d for d in single if d.partname == device.partname]
        if len(single) != 1:
            raise VerificationError(
                f"{path.name}: Device '{device.partname}' is not unique in its device tree!"
            )
        merged_properties, single_properties = device.properties, single[0].properties
        if _canonical(merged_properties, True) != _canonical(single_properties, True):
            raise VerificationError(
                f"{path.name}: Merged properties of '{device.partname}' differ!"
            )
        if _canonical(merged_properties, False) != _canonical(single_properties, False):
            duplicates.append(device.partname)
    return partnames, duplicates


def generate_device_files(
    trees: dict, merger, output: Path, verify: bool = True
) -> list[Path]:
    """
    Merges device trees, writes them as device files, and optionally verifies
    that the merged files describe every device identically to its unmerged tree.

    :param trees: Mapping of name to device tree, which may contain multiple devices.
    :param merger: Function merging a list of device trees into a list of `(filename, tree)`.
    :param output: The folder to write the device files into.
    :param verify: Verify the merged files against the unmerged device trees.
    :return: A list of written device file paths.
    """
    originals = {}
    if verify:
        for tree in trees.values():
            copy = tree.copy()
            originals.update((did.string, copy) for did in copy.ids)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    paths = []
    verified = set()
    for filename, tree in merger(list(trees.values())):
        path = output / f"{filename}.xml"
        if path in paths:
            raise VerificationError(
                f"Device file '{path.name}' was generated multiple times!"
            )
        path.write_bytes(format_device_file(tree))
        LOGGER.info("Generated '%s'", path.name)
        paths.append(path)
        if verify:
            partnames, duplicates = verify_device_file(path, originals)
            verified.update(partnames)
            if duplicates:
                LOGGER.warning(
                    "%s: %d devices contain duplicated items!",
                    path.name,
                    len(duplicates),
                )

    if verify and (missing := set(originals) - verified):
        raise VerificationError(
            f"Devices missing from the device files: {sorted(missing)}"
        )
    return paths
