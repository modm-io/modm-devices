# Copyright 2026, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

"""
# modm Device File Generator

Converts the device data extracted by modm-data into modm device files, which
are merged XML files describing multiple similar devices.

Merging devices into one file can hide or introduce data errors. Therefore,
every merged device file is verified by parsing it and comparing the properties
of each contained device with its unmerged device tree.

The data pipelines of [modm-data](https://github.com/modm-io/modm-data) must be
installed including their input sources:

```sh
python3 -m dfg all
```
"""

import sys
from pathlib import Path

# The modm_devices parser package is located in the repository root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .identifier import MultiDeviceIdentifier  # noqa: E402
from .tree import DeviceTree  # noqa: E402
from .merger import merge, group_index  # noqa: E402
from .writer import format_device_file, write_device_file  # noqa: E402
from .generator import generate_device_files, verify_device_file, VerificationError  # noqa: E402

__all__ = [
    "MultiDeviceIdentifier",
    "DeviceTree",
    "merge",
    "group_index",
    "format_device_file",
    "write_device_file",
    "generate_device_files",
    "verify_device_file",
    "VerificationError",
]
