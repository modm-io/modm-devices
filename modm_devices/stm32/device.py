#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

from .gpio import DriverGpio
from .core import DriverCore
from .flash import DriverFlash
from ..device import Device
from ..cache import cached_property
from ..access import copy_keys


class Stm32Device(Device):
    def __init__(self, identifier, device_file):
        Device.__init__(self, identifier, device_file)

    @cached_property
    def gpio(self):
        return DriverGpio(self)

    @cached_property
    def core(self):
        return DriverCore(self)

    @cached_property
    def flash(self):
        return DriverFlash(self)

    @cached_property
    def peripherals(self):
        all_peripherals = []
        for s in self.gpio.signals_all:
            d = copy_keys(s, "driver", "instance")
            if len(d): all_peripherals.append(d);

        # Signals are not enough, since there are peripherals that don't have signals.
        # Example: STM32F401RE < 64pins: SPI4 cannot be connected to any pins.
        for d in self._properties["driver"]:
            driver = d["name"]
            if driver in ["gpio", "core"]:
                continue
            elif "instance" in d:
                all_peripherals.extend( {"driver": driver, "instance": int(i["name"])} for i in d["instance"] )
            else:
                all_peripherals.append( {"driver": driver} )

        for r in self.gpio._driver.get("remap", {}):
            d = copy_keys(r, "driver", "instance")
            if len(d): all_peripherals.append(d);

        return all_peripherals
