#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parser for the device files.
"""

import itertools

from . import pkg
from .common import ParserException

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
                xsdfile = pkg.get_filename('device', 'resources/schema/device.xsd')

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
        
        platform = node.attrib["platform"]
        family = node.attrib["family"]
        device_name = node.attrib.get("name", "").split('|')
        device_type = node.attrib.get("type", "").split('|')
        pin_id = node.attrib.get("pin_id", "").split('|')
        size_id = node.attrib.get("size_id", "").split('|')
        
        if platform == "stm32":
            devices = list(itertools.product((platform,), ("f",), device_name, pin_id, size_id))
        elif family == "at90":
            devices = list(itertools.product((family,), device_type, device_name))
        elif family == "xmega":
            devices = list(itertools.product(("at" + family,), device_name, device_type, pin_id))
        elif family == "atmega" or family == "attiny":
            devices = list(itertools.product((family,), device_name, device_type))
        elif platform == "lpc":
            devices = list(itertools.product((platform,), (family,), device_name))
        elif platform == "hosted":
            devices = list(itertools.product((platform,), (family,)))
        
        device_name_list = []
        for device in devices:
            device_name_list.append("".join(device).replace("none", ""))
        
        return device_name_list
