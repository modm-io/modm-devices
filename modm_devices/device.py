#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import copy
import itertools

from .exception import ParserException
from .device_identifier import DeviceIdentifier
from .driver import Driver
from .cache import *
import fnmatch

class Device:
    def __init__(self,
                 identifier: DeviceIdentifier,
                 device_file):
        self._identifier = identifier.copy()
        self.partname = identifier.string
        self._device_file = device_file
        self.__properties = None

    @property
    def _properties(self):
        if self.__properties is None:
            self.__properties = self._device_file.get_properties(self._identifier)
        return self.__properties

    def _find_drivers(self, *patterns):
        results = []
        for pattern in patterns:
            parts = pattern.split(":")

            if len(parts) == 1:
                results.extend(d for d in self._properties["driver"]
                               if fnmatch.fnmatch(d["name"], parts[0]))
            elif len(parts) == 2:
                results.extend(d for d in self._properties["driver"]
                               if (fnmatch.fnmatch(d["name"], parts[0]) and
                                   fnmatch.fnmatch(d["type"], parts[1])))
            else:
                raise ParserException("Invalid driver pattern '{}'. "
                                      "The name must contain no or one ':' to "
                                      "separate `name:type` pattern.".format(parts))

        return results

    def _find_first_driver(self, *patterns):
        results = self._find_drivers(*patterns)
        return results[0] if len(results) else None

    @property
    def did(self):
        return self._identifier

    @cached_function
    def driver(self, name):
        return Driver(self, self._find_first_driver(name))

    def drivers(self, *names):
        return [Driver(self, d) for d in self._find_drivers(*names)]

    def has_driver(self, *names):
        return len(self._find_drivers(*names))

    # Deprecated stuff
    def get_driver(self, pattern):
        return self._find_first_driver(pattern)

    def get_all_drivers(self, *patterns):
        return self._find_drivers(*patterns)

    @property
    def identifier(self):
        return self.did
