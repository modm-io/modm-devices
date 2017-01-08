#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2017, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import lxml.etree

from collections import defaultdict

from modm.device import Device
from modm.device_identifier import DeviceIdentifier
from modm.device_identifier import MultiDeviceIdentifier

from .common import ParserException

class DeviceFile:
    _DEVICE_ATTRIBUTE_PREFIX = 'device-'

    def __init__(self, filename, rootnode):
        self.filename = filename
        self.rootnode = rootnode

    def _get_multi_device_identifier(self, node, naming_schema):
        properties = {k:v.split("|") for k,v in node.attrib.items()}
        return MultiDeviceIdentifier.from_product(properties, naming_schema)

    def get_devices(self):
        """
        Return a list of devices which are covered by this device file.
        """
        device_node = self.rootnode.find('device')
        naming_schema_string = device_node.find('naming-schema').text
        identifiers = self._get_multi_device_identifier(device_node, naming_schema_string)

        # Not all combinations which can be generated through the
        # naming schema are valid. Grab the list of excluded device names
        # to remove those from the constructed devices.
        invalid_devices = [node.text for node in device_node.iterfind('invalid-device')]
        valid_devices = [node.text for node in device_node.iterfind('valid-device')]
        devices = identifiers
        if len(invalid_devices):
            devices = [did for did in devices if did.string not in invalid_devices]
        if len(valid_devices):
            devices = [did for did in devices if did.string in valid_devices]
        return [Device(did, self) for did in devices]

    @staticmethod
    def is_valid(node, identifier: DeviceIdentifier):
        """
        Read and removes the selector attributes and match them against the
        device identifier.

        Returns:
            True if the selectors match, False otherwise.
        """
        device_keys = [k for k in node.attrib.keys() if k.startswith(DeviceFile._DEVICE_ATTRIBUTE_PREFIX)]
        properties = {k.replace(DeviceFile._DEVICE_ATTRIBUTE_PREFIX, ''):node.attrib[k].split("|") for k in device_keys}
        for k in device_keys:
            del node.attrib[k]
        return not any(identifier[key] not in value for key, value in properties.items())

    def get_properties(self, identifier: DeviceIdentifier):
        class Converter:
            """
            Convert XML to a Python dictionary according to
            http://www.xml.com/pub/a/2006/05/31/converting-between-xml-and-json.html
            """
            def __init__(self, identifier: DeviceIdentifier):
                self.identifier = identifier

            def is_valid(self, node):
                return DeviceFile.is_valid(node, self.identifier)

            def to_dict(self, t):
                if isinstance(t, lxml.etree._Comment):
                    # Remove comments in the XML file from the generated dict.
                    return {}
                d = {t.tag: {} if t.attrib else None}
                children = []
                for c in t:
                    if self.is_valid(c):
                        children.append(c)
                if children:
                    dd = defaultdict(list)
                    for dc in map(self.to_dict, children):
                        for k, v in dc.items():
                            dd[k].append(v)
                    d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
                if t.attrib.keys() == ['value']:
                    d[t.tag] = t.attrib['value']
                elif t.attrib:
                    d[t.tag].update((k, v) for k, v in t.attrib.items())
                return d

        properties = Converter(identifier).to_dict(self.rootnode.find("device"))
        return properties["device"]
