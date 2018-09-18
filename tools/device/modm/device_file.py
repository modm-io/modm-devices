#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2017, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import lxml.etree

from collections import defaultdict

from .device import Device
from .device_identifier import DeviceIdentifier
from .device_identifier import MultiDeviceIdentifier

from .exception import ParserException

class DeviceFile:
    _PREFIX_ATTRIBUTE = 'attribute-'
    _PREFIX_ATTRIBUTE_DEVICE = 'device-'
    _INVALID_DEVICE = 'invalid-device'
    _VALID_DEVICE = 'valid-device'


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
        invalid_devices = [node.text for node in device_node.iterfind(self._INVALID_DEVICE)]
        valid_devices = [node.text for node in device_node.iterfind(self._VALID_DEVICE)]
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
        device_keys = filter(lambda k: k.startswith(DeviceFile._PREFIX_ATTRIBUTE_DEVICE), node.attrib.keys())
        properties = {k.replace(DeviceFile._PREFIX_ATTRIBUTE_DEVICE, ''):node.attrib[k].split("|") for k in device_keys}
        return not any(identifier[key] not in value for key, value in properties.items())

    def get_properties(self, identifier: DeviceIdentifier):
        class Converter:
            """
            """
            def __init__(self, identifier: DeviceIdentifier):
                self.identifier = identifier

            def is_valid(self, node):
                ignored = [DeviceFile._VALID_DEVICE, DeviceFile._INVALID_DEVICE, 'naming-schema']
                if (node.getparent().getparent().getparent() is None and
                    node.getparent().tag == 'device' and
                    node.tag in ignored):
                    return False
                return DeviceFile.is_valid(node, self.identifier)

            def strip_attrib(self, node):
                stripped_keys = filter(lambda k: not k.startswith(DeviceFile._PREFIX_ATTRIBUTE_DEVICE), node.attrib.keys())
                if node.getparent().getparent() is None and node.tag == 'device':
                    stripped_keys = filter(lambda k: k not in self.identifier.keys(), stripped_keys)
                return {k:node.attrib[k] for k in stripped_keys}

            def to_dict(self, t):
                if isinstance(t, lxml.etree._Comment):
                    # Remove comments in the XML file from the generated dict.
                    return {}
                attrib = self.strip_attrib(t)
                d = {t.tag: {} if len(attrib) else None}
                children = []
                for c in t:
                    if self.is_valid(c):
                        children.append(c)
                if children:
                    dd = defaultdict(list)
                    for dc in map(self.to_dict, children):
                        for k, v in dc.items():
                            dd[k].append(v)
                    dk = {}
                    for k, v in dd.items():
                        if k.startswith(DeviceFile._PREFIX_ATTRIBUTE):
                            if len(v) > 1:
                                raise ParserException("Attribute '{}' cannot be a list!".format(k))
                            k = k.replace(DeviceFile._PREFIX_ATTRIBUTE, '')
                            v = v[0]
                        dk[k] = v
                    d = {t.tag: dk}
                if list(attrib.keys()) == ['value']:
                    d[t.tag] = attrib['value']
                elif len(attrib):
                    if any(k in d[t.tag] for k in attrib.keys()):
                        raise ParserException("Node children are overwriting attribute '{}'!".format(k))
                    d[t.tag].update(attrib.items())
                return d

        properties = Converter(identifier).to_dict(self.rootnode.find("device"))
        return properties["device"]
