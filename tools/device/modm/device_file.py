#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

    def _is_valid(self, node, identifier):
        """
        Read the selector attributes and match them against the device
        identifier.

        Returns:
            True if the selectors match, False otherwise.
        """
        selector = modm.device.Selector()
        for attribute_name, property_name in self._ATTRIBUTE_PROPERTY_MAPPING.items():
            value = node.attrib.get(attribute_name, "")
            values = value.split("|")
            if len(values) > 1 or values[0] != '':
                selector.property[property_name] = values

        return selector.match(identifier)

    def _node_to_dict(self, node, identifier):
        node_dict = {}
        if self._is_valid(node, identifier):
            # Fist add attributes
            for key, value in node.items():
                if key not in self._ATTRIBUTE_PROPERTY_MAPPING.keys():
                    node_dict[key] = value
            # Add content
            if node.text is not None and not node.text.isspace():
                node_dict['value'] = node.text
            # Now add children
            for child_node in node:
                child_name = child_node.tag + 's'
                if child_name not in node_dict:
                    # create child_node list
                    node_dict[child_name] = []

                child_dict = self._node_to_dict(child_node, identifier)
                if len(child_dict) > 0:
                    node_dict[child_name].append(child_dict)
        return node_dict

    def get_properties(self, identifier: modm.device.DeviceIdentifier):
        properties = {}
        for tag in ["driver", "flash", "ram", "core", "pin-count", "eeprom", "mcu", "header", "define"]:
            for property_node in self.rootnode.iterfind("/".join(["device", tag])):
                if self._is_valid(property_node, identifier):
                    propertey_list = properties.get(tag, [])
                    propertey_list.append(self._node_to_dict(property_node, identifier))
                    properties[tag] = propertey_list
        return properties
