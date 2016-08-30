#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parser for the device files.
"""

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
