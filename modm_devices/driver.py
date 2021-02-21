#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Niklas Hauser
# All rights reserved.

from collections import defaultdict
from .cache import *

class Instance:
    def __init__(self, driver, instance):
        self._instance = instance
        self.driver = driver
        self.name = self._instance["name"]
        self.number = int(self.name) if self.name.isdigit() else self.name

    def features(self, default=[]):
        feats = self.driver.features()
        feats.extend(self._instance.get("feature", []))
        return feats if len(feats) else default

    def __str__(self):
        return self.name


class Driver:
    def __init__(self, device, driver):
        self._driver = driver
        self.device = device
        self.name = self._driver["name"]
        self.type = self._driver["type"]

    def instances(self, default=[]):
        if "instance" in self._driver:
            return [Instance(self, i) for i in self._driver["instance"]]
        return default

    def features(self, default=[]):
        if "feature" in self._driver:
            return list(self._driver["feature"])
        return default

    def __str__(self):
        return self.name
