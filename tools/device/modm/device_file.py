#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict

import modm.name
import modm.device

from .common import ParserException

class DeviceFile:

    # Mapping for the XML attributes to the properties of the device selector
    _ATTRIBUTE_PROPERTY_MAPPING = {
        "device-platform": "platform",
        "device-family": "family",
        "device-name": "name",
        "device-type": "type",
        "device-pin-id": "pin_id",
        "device-size-id": "size_id",
    }

    def __init__(self, filename, rootnode):
        self.filename = filename
        self.rootnode = rootnode

    def _get_multi_device_identifier(self, node):
        identifier = modm.device.MultiDeviceIdentifier()
        for key in identifier.__dict__:
            setattr(identifier,
                    key,
                    node.attrib.get(key, "").replace("none", "").split('|'))
        return identifier

    def get_devices(self):
        """
        Return a list of devices which are covered by this device file.
        """
        device_node = self.rootnode.find('device')
        identifiers = self._get_multi_device_identifier(device_node)

        # Not all combinations which can be generated through the
        # naming schema are valid. Grab the list of excluded device names
        # to remove those from the constructed devices.
        invalid_devices = []
        for node in device_node.iterfind('invalid-device'):
            invalid_devices.append(node.text)

        naming_schema_string = device_node.find('naming-schema').text
        naming_schema = modm.name.Schema.parse(naming_schema_string)

        attributes = identifiers.check_attributes(naming_schema)
        if len(attributes) > 0:
            raise ParserException("The following attributes are defined but not used "
                                  "by the naming schema: '{}'".format("', '".join(attributes)))
        device_name_list = []
        for device_identifier in identifiers.get_devices():
            device = modm.device.Device(device_identifier, naming_schema, self)

            if device.partname not in invalid_devices:
                device_name_list.append(device)

        return device_name_list

    @staticmethod
    def is_valid(node, identifier: modm.device.DeviceIdentifier):
        """
        Read and removes the selector attributes and match them against the
        device identifier.
        
        Returns:
            True if the selectors match, False otherwise.
        """
        selector = modm.device.Selector()
        for attribute_name, property_name in DeviceFile._ATTRIBUTE_PROPERTY_MAPPING.items():
            value = node.attrib.get(attribute_name, "")
            values = value.split("|")
            if len(values) > 1 or values[0] != '':
                selector.property[property_name] = values
                del node.attrib[attribute_name]
        return selector.match(identifier)

    def get_properties(self, identifier: modm.device.DeviceIdentifier):
        class Converter:
            """
            Convert XML to a Python dictionary according to
            http://www.xml.com/pub/a/2006/05/31/converting-between-xml-and-json.html
            """
            def __init__(self, identifier: modm.device.DeviceIdentifier):
                self.identifier = identifier

            def is_valid(self, node):
                return DeviceFile.is_valid(node, self.identifier)

            def to_dict(self, t):
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
                if t.attrib:
                    d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
                if t.text:
                    text = t.text.strip()
                    if children or t.attrib:
                        if text:
                            d[t.tag]['#text'] = text
                    else:
                        d[t.tag] = text
                return d

        properties = Converter(identifier).to_dict(self.rootnode.find("device"))
        return properties["device"]
