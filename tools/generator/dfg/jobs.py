# Copyright 2026, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

import time
import logging
import importlib
import traceback
from pathlib import Path

from .generator import generate_device_files

# Devices are only merged within one job, which may contain multiple prefixes
JOBS = {
    "stm32": [
        [f"stm32{family}"]
        for family in "c0 f0 f1 f2 f3 f4 f7 g0 g4 h5 h7 l0 l1 l4 l5 u0 u3 u5 wb wl".split()
    ],
    "avr": [["at90"], ["attiny"], ["atmega"]],
    "sam": [
        ["samda"],
        ["samd1"],
        ["samd2"],
        ["samd09"],
        ["saml2"],
        ["samg5"],
        ["samd5", "same5"],
        ["same7", "sams7", "samv7"],
    ],
    "nrf": [["nrf51"], ["nrf52"], ["nrf53"]],
    "rp": [["rp2040"], ["rp2350"]],
}

# Vendor modules implementing `PLATFORM`, `device_trees()` and `merge_device_trees()`
VENDORS = {
    "stm32": "dfg.stmicro",
    "at": "dfg.avr",
    "sam": "dfg.sam",
    "nrf": "dfg.nordic",
    "rp": "dfg.raspberrypi",
}


def vendor_module(prefix: str):
    """
    :param prefix: A device prefix, for example, `stm32f4` or `attiny`.
    :return: The vendor module that generates device trees for this prefix.
    """
    for vendor_prefix, module in VENDORS.items():
        if prefix.startswith(vendor_prefix):
            return importlib.import_module(module)
    raise ValueError(f"Unknown device prefix '{prefix}'!")


def expand_targets(targets: list[str]) -> list[list[str]]:
    """
    :param targets: Device prefixes (comma-separated to merge them together), vendor names, or `all`.
    :return: A list of jobs, each a list of device prefixes merged together.
    """
    jobs = []
    for target in targets:
        if target == "all":
            jobs.extend(job for vendor_jobs in JOBS.values() for job in vendor_jobs)
        elif target in JOBS:
            jobs.extend(JOBS[target])
        else:
            jobs.append(target.split(","))
    return jobs


def generate_job(
    job: list[str], output: Path, verify: bool = True, log_level: str = "WARNING"
):
    """
    Generates the device files of one job. Suitable for running in a worker process.

    :return: Tuple of the job, number of devices, list of paths, duration in seconds, and error string.
    """
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(name)s: %(message)s")
    try:
        start = time.time()
        vendor = vendor_module(job[0])
        folder = Path(output) / vendor.PLATFORM
        for prefix in job:
            for path in folder.glob(f"{prefix}*.xml"):
                path.unlink()
        trees = vendor.device_trees(job)
        paths = generate_device_files(
            trees, vendor.merge_device_trees, folder, verify=verify
        )
        return job, len(trees), paths, time.time() - start, None
    except Exception:
        return job, 0, [], 0, traceback.format_exc()
