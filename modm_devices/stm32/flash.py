#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Niklas Hauser
# All rights reserved.

from ..cache import cached_property
from ..driver import Driver
from collections import defaultdict

class DriverFlash(Driver):
    def __init__(self, device):
        Driver.__init__(self, device, device._find_first_driver("flash"))


    @cached_property
    def wait_states(self):
        """
        :return: a map from int(min Vcore): [int(max F) for 0 wait states, ..., int(max F) for N wait states].
        """
        states = {}
        for vcore in self._driver.get("latency", []):
            states[int(vcore["vcore-min"])] = sorted([int(f["hclk-max"]) for f in vcore["wait-state"]])
        return states
