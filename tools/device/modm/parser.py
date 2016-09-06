#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parser for the modm files.
"""

import itertools
from . import pkg
from .common import ParserException

import modm.device

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
        
        devices = modm.device.Device()
        
        devices.platform = node.attrib["platform"].split('|')
        devices.family = node.attrib["family"].split('|')
        devices.name = node.attrib.get("name", "").split('|')
        devices.type = node.attrib.get("type", "").split('|')
        devices.pin_id = node.attrib.get("pin_id", "").split('|')
        devices.size_id = node.attrib.get("size_id", "").split('|')
        
        class Attribute:
            def __init__(self, name):
                self.name = name
            def get(self, device):
                return getattr(device, self.name)
            def set(self, device, value):
                setattr(device, self.name, value)
        
        class Fixed:
            def __init__(self, name):
                self.name = name
            def get(self, devices):
                return (self.name,)
            def set(self, device, value):
                pass
        
        if devices.platform[0] == "stm32":
            naming_schema = [
               Attribute("platform"),
               Fixed("f"),
               Attribute("name"),
               Attribute("pin_id"),
               Attribute("size_id"),
            ]
        elif devices.family[0] == "at90":
            naming_schema = [
               Attribute("family"),
               Attribute("type"),
               Attribute("name"),
            ]
        elif devices.family[0] == "xmega":
            naming_schema = [
               Fixed("at"),
               Attribute("family"),
               Attribute("name"),
               Attribute("type"),
               Attribute("pin_id"),
            ]
        elif devices.family[0] == "atmega" or devices.family[0] == "attiny":
            naming_schema = [
               Attribute("family"),
               Attribute("name"),
               Attribute("type"),
            ]
        elif devices.platform[0] == "lpc":
            naming_schema = [
               Attribute("platform"),
               Attribute("family"),
               Attribute("name"),
            ]
        elif devices.platform[0] == "hosted":
            naming_schema = [
               Attribute("platform"),
               Fixed("/"),
               Attribute("family"),
            ]
        
        devices = list(itertools.product(*[token.get(devices) for token in naming_schema]))

        device_name_list = []
        for device_parts in devices:
            device = modm.device.Device()
            partname = []
            for token, value in zip(naming_schema, device_parts):
                v = value.replace("none", "")
                token.set(device, v)
                partname.append(v)
            
            device.partname = "".join(partname)
            device_name_list.append(device)
        
        return device_name_list
