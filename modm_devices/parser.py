#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# All rights reserved.
"""
XML parser for the modm files.
"""

from . import pkg
from .device_file import DeviceFile

from .exception import ParserException

# lxml must be imported **after** the Catalog file have been set by 'pkg', otherwise
# it runs into an endless loop during verification.
import lxml.etree


class Parser:
    def __init__(self, xsdfile):
        self.xsdfile = xsdfile

    @staticmethod
    def validate_and_parse_xml(filename, xsdfile):
        try:
            # parse the xml-file
            parser = lxml.etree.XMLParser(no_network=True)
            xmlroot = lxml.etree.parse(filename, parser=parser)
            xmlroot.xinclude()

            xmlschema = lxml.etree.parse(xsdfile, parser=parser)

            schema = lxml.etree.XMLSchema(xmlschema)
            # schema.assertValid(xmlroot)

            rootnode = xmlroot.getroot()
        except OSError as error:
            raise ParserException(error)
        except (lxml.etree.DocumentInvalid,
                lxml.etree.XMLSyntaxError,
                lxml.etree.XMLSchemaParseError,
                lxml.etree.XIncludeError) as error:
            raise ParserException("While parsing '{}':"
                                  " {}".format(error.error_log.last_error.filename,
                                               error))
        return rootnode


class DeviceParser(Parser):
    def __init__(self):
        Parser.__init__(self,
                        pkg.get_filename('modm_devices', 'resources/schema/device.xsd'))

    def parse(self, filename):
        rootnode = self.validate_and_parse_xml(filename, self.xsdfile)
        return DeviceFile(filename, rootnode)


class DriverParser(Parser):
    def __init__(self):
        Parser.__init__(self,
                        xsdfile=pkg.get_filename('modm_devices', 'resources/schema/driver.xsd'))

    def parse(self, filename):
        rootnode = self.validate_and_parse_xml(filename, self.xsdfile)
        return rootnode

