#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2017, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import lxml.etree
import copy

from collections import defaultdict

from .device import Device
from .stm32.device import Stm32Device
from .device_identifier import DeviceIdentifier
from .device_identifier import MultiDeviceIdentifier
from .access import read_only

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
            devices = (did for did in devices if did.string not in invalid_devices)
        if len(valid_devices):
            devices = (did for did in devices if did.string in valid_devices)
        def build_device(did, device_file):
            if did.platform == "stm32":
                return Stm32Device(did, device_file)
            return Device(did, device_file)
        return [build_device(did, self) for did in devices]

    @staticmethod
    def is_valid(node, identifier: DeviceIdentifier):
        """
        Read and removes the selector attributes and match them against the
        device identifier.

        Returns:
            True if the selectors match, False otherwise.
        """
        device_keys = (k for k in node.attrib.keys() if k.startswith(DeviceFile._PREFIX_ATTRIBUTE_DEVICE))
        properties = ((k.replace(DeviceFile._PREFIX_ATTRIBUTE_DEVICE, ''), node.attrib[k].split("|"))
                      for k in device_keys)
        return all(identifier[key] in value for key, value in properties)

    def get_properties(self, identifier: DeviceIdentifier):
        class Converter:
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
                stripped_keys = (k for k in node.attrib.keys() if not k.startswith(DeviceFile._PREFIX_ATTRIBUTE_DEVICE))
                if node.getparent().getparent() is None and node.tag == 'device':
                    stripped_keys = (k for k in stripped_keys if k not in self.identifier.keys())
                return {k:node.attrib[k] for k in stripped_keys}

            def to_dict(self, t):
                if isinstance(t, lxml.etree._Comment):
                    # Remove comments in the XML file from the generated dict.
                    return {}
                attrib = self.strip_attrib(t)
                d = {t.tag: {} if len(attrib) else None}
                children = filter(self.is_valid, t)
                if children:
                    dd = defaultdict(list)
                    for dc in map(self.to_dict, children):
                        # print(dc)
                        for k, v in dc.items():
                            # if k == "signal" and v.get("name") == "seg40": print(v)
                            dd[k].append(v)
                    dk = {}
                    for k, v in dd.items():
                        if k.startswith(DeviceFile._PREFIX_ATTRIBUTE):
                            if len(v) > 1:
                                raise ParserException("Attribute '{}' cannot be a list!".format(k))
                            k = k.replace(DeviceFile._PREFIX_ATTRIBUTE, '')
                            v = v[0]
                        dk[k] = read_only(v)
                    d = {t.tag: dk}
                if list(attrib.keys()) == ['value']:
                    d[t.tag] = attrib['value']
                elif len(attrib):
                    if any(k in d[t.tag] for k in attrib.keys()):
                        raise ParserException("Node children are overwriting attribute '{}'!".format(k))
                    # print(attrib.items())
                    d[t.tag].update(attrib.items())
                return read_only({k:read_only(v) for k,v in d.items()})

        properties = Converter(identifier).to_dict(self.rootnode.find("device"))
        # print(properties)
        # exit(1)
        return properties["device"]
