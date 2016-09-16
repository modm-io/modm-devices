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

    def parse(self, filename, xsdfile=None):
        rootnode = self._validate_and_parse_xml(filename, xsdfile)

        return rootnode

    @staticmethod
    def _validate_and_parse_xml(filename, xsdfile):
        try:
            # parse the xml-file
            parser = lxml.etree.XMLParser(no_network=True)
            xmlroot = lxml.etree.parse(filename, parser=parser)
            xmlroot.xinclude()

            if xsdfile is None:
                xsdfile = pkg.get_filename('modm', 'resources/schema/device.xsd')

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

    def get_devices(self, rootnode):
        node = rootnode.find('device')

        identifiers = modm.device.MultiDeviceIdentifier()

        def replace_none(node):
            return "" if (node == "none") else node

        identifiers.platform = list(map(replace_none, node.attrib["platform"].split('|')))
        identifiers.family = list(map(replace_none, node.attrib["family"].split('|')))
        identifiers.name = list(map(replace_none, node.attrib.get("name", "").split('|')))
        identifiers.type = list(map(replace_none, node.attrib.get("type", "").split('|')))
        identifiers.pin_id = list(map(replace_none, node.attrib.get("pin_id", "").split('|')))
        identifiers.size_id = list(map(replace_none, node.attrib.get("size_id", "").split('|')))

        if identifiers.platform[0] == "stm32":
            naming_schema_string = "{{ platform }}f{{ name }}{{ pin_id }}{{ size_id }}"
        elif identifiers.family[0] == "at90":
            naming_schema_string = "{{ family }}{{ type }}{{ name }}"
        elif identifiers.family[0] == "xmega":
            naming_schema_string = "at{{ family }}{{ name }}{{ type }}{{ pin_id }}"
        elif identifiers.family[0] == "atmega" or identifiers.family[0] == "attiny":
            naming_schema_string = "{{ family }}{{ name }}{{ type }}"
        elif identifiers.platform[0] == "lpc":
            naming_schema_string = "{{ platform }}{{ family }}{{ name }}"
        elif identifiers.platform[0] == "hosted":
            naming_schema_string = "{{ platform }}/{{ family }}"

        naming_schema = modm.name.Schema.parse(naming_schema_string)

        device_name_list = []
        for device_identifier in identifiers.get_devices():
            device = modm.device.Device(device_identifier, naming_schema)
            device_name_list.append(device)

        return device_name_list
