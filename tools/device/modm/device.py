#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools

from . import name

class DeviceIdentifier:
    """
    Unique identifier of a specific target device.
    
    Not all a attributes are set for all devices.
    """
    def __init__(self):
        self.platform = None
        self.family = None
        self.name = None
        self.type = None
        self.pin_id = None
        self.size_id = None

    @staticmethod
    def _listify(node):
        if isinstance(node, list) or isinstance(node, tuple):
            return node
        else:
            return (node,)

    def as_list(self, as_tuple=True):
        if as_tuple:
            return (self._listify(self.platform),
                    self._listify(self.family),
                    self._listify(self.name),
                    self._listify(self.type),
                    self._listify(self.pin_id),
                    self._listify(self.size_id),)
        else:
            return (self.platform,
                    self.family,
                    self.name,
                    self.type,
                    self.pin_id,
                    self.size_id,)

    @staticmethod
    def from_list(attribute_list):
        identifier = DeviceIdentifier()

        identifier.platform = attribute_list[0]
        identifier.family = attribute_list[1]
        identifier.name = attribute_list[2]
        identifier.type = attribute_list[3]
        identifier.pin_id = attribute_list[4]
        identifier.size_id = attribute_list[5]

        return identifier


class MultiDeviceIdentifier(DeviceIdentifier):
    """
    Identifier for a group of devices.
    
    For the multi device identifier the attributes are not a single
    string but rather a list of string. Can be split into separate devices.
    """
    def __init__(self):
        DeviceIdentifier.__init__(self)

    def get_devices(self):
        """
        Split into separate device identifiers.
        """
        identifiers = list(itertools.product(*self.as_list(as_tuple=True)))
        device_list = []
        for identifier in identifiers:
            device_identifier = DeviceIdentifier.from_list(identifier)
            device_list.append(device_identifier)
        return device_list

class Device:
    def __init__(self, identifier, naming_schema):
        self.identifier = identifier
        self.naming_schema = naming_schema
        self.partname = naming_schema.get_name(identifier)

    def __str__(self):
        return self.partname

class Selector:
    def __init__(self):
        self.property = {
            "platform": [],
            "family": [],
            "name": [],
            "type": [],
            "pin_id": [],
            "size_id": []
        }

    def match(self, device_identifier):
        for key, values in self.property.items():
            if values is None or len(values) == 0:
                continue

            if getattr(device_identifier, key) not in values:
                return False
        return True
