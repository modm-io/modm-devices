#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# All rights reserved.
"""
XML parser for the modm files.
"""

from . import pkg
from .common import ParserException

import modm.device
import modm.name

# lxml must be imported **after** the Catalog file have been set by 'pkg', otherwise
# it runs into an endless loop during verification.
import lxml.etree


class Parser:
    def __init__(self, filename, xsdfile):
        self.rootnode = self.validate_and_parse_xml(filename, xsdfile)

    @staticmethod
    def validate_and_parse_xml(filename, xsdfile):
        try:
            # parse the xml-file
            parser = lxml.etree.XMLParser(no_network=True)
            xmlroot = lxml.etree.parse(filename, parser=parser)
            xmlroot.xinclude()

            xmlschema = lxml.etree.parse(xsdfile, parser=parser)

            schema = lxml.etree.XMLSchema(xmlschema)
            schema.assertValid(xmlroot)

            rootnode = xmlroot.getroot()
        except OSError as error:
            raise ParserException(error)
        except (lxml.etree.DocumentInvalid,
                lxml.etree.XMLSyntaxError,
                lxml.etree.XMLSchemaParseError,
                lxml.etree.XIncludeError) as error:
            raise ParserException("While parsing '%s': %s"
                                  % (error.error_log.last_error.filename, error))
        return rootnode

class DeviceParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self,
                        filename,
                        pkg.get_filename('modm', 'resources/schema/device.xsd'))

    def get_devices(self):
        device_node = self.rootnode.find('device')
        identifiers = modm.device.MultiDeviceIdentifier.from_xml(device_node)

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
            device = modm.device.Device(device_identifier, naming_schema)

            if device.partname not in invalid_devices:
                device_name_list.append(device)

        return device_name_list

class DriverParser(Parser):
    def __init__(self, filename):
        Parser.__init__(self,
                        filename,
                        xsdfile=pkg.get_filename('modm', 'resources/schema/driver.xsd'))
