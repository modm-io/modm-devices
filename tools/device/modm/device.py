#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import copy
import itertools

from .common import ParserException
from .device_identifier import DeviceIdentifier


class Device:
    def __init__(self,
                 identifier: DeviceIdentifier,
                 device_file):
        self._identifier = identifier.copy()
        self.naming_schema = identifier.naming_schema
        self.partname = identifier.string
        self.device_file = device_file

        self._properties = None

    def __parse_properties(self):
        """
        Perform a lazy initialization of the driver property tree.
        """
        if self._properties is None:
            self._properties = self.device_file.get_properties(self._identifier)

    @property
    def properties(self):
        self.__parse_properties()
        return copy.deepcopy(self._properties)

    @property
    def identifier(self):
        return copy.deepcopy(self._identifier.properties)

    def get_driver(self, name):
        self.__parse_properties()

        parts = name.split(":")
        if len(parts) == 1:
            for driver in self._properties["driver"]:
                if driver["type"] == parts[0]:
                    return driver
        elif len(parts) == 2:
            for driver in self._properties["driver"]:
                if driver["type"] == parts[0] and driver["compatible"] == parts[1]:
                    return driver
        else:
            raise ParserException("Invalid driver name '{}'. "
                                  "The name must contain no or one ':' to "
                                  "separate type and name.".format(name))

    def has_driver(self, name, compatible: list = []):
        if len(compatible) == 0:
            return self.get_driver(name) is not None

        if ':' in name:
            raise ParserException("Invalid driver name '{}'. "
                                  "The name must contain no ':' when using the "
                                  "compatible argument.".format(name))

        return any(self.get_driver(name + ':' + c) is not None for c in compatible)

    def __str__(self):
        return self.partname
