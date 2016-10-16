# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import logging

from .reader import XMLDeviceReader
from .identifiers import Identifiers

LOGGER = logging.getLogger('dfg.device')

class Device:
    """ Device
    Represents a device.
    """

    def __init__(self, description_file=None):
        self.ids = None
        self.properties = []
        if description_file == None:
            self.ids = Identifiers(None)
            return

        # proper handling of Parsers
        if isinstance(description_file, XMLDeviceReader):
            self.properties = list(description_file.properties)
            self.ids = Identifiers(description_file.id)
        else:
            self.properties = list(description_file)

        if self.ids == None:
            self.ids = Identifiers(None)

        # if flash or ram is missing, it is a bad thing and unsupported
        if self.getProperty('flash') == None:
            LOGGER.error("No FLASH found")
            return None
        if self.getProperty('ram') == None:
            LOGGER.error("No RAM found")
            LOGGER.error("XPCC does not support Assembler-only programming!")
            return None
        # eeprom is optional on AVR and not available on ARM devices
        if (self.getProperty('eeprom') == None) and ('avr' == self.id.platform):
            LOGGER.warning("No EEPROM found")

    def getMergedDevice(self, other):
        """
        Merges the values of both devices and add a dictionary of differences
        """
        assert isinstance(other, Device)
        LOGGER.info("Merging '%s'  with  '%s'", self.ids.string, other.ids.string)

        # update the ids in both
        self.ids.extend(other.ids)

        # go through all properties and merge each one
        for self_property in self.properties:
            for other_property in other.properties:
                if self_property.name == other_property.name:
                    self_property = self_property.getMergedProperty(other_property)

        self.properties.sort(key=lambda k : k.name)

        return self;

    @property
    def id(self):
        return self.ids.intersection

    def getProperty(self, name):
        for prop in self.properties:
            if prop.name == name:
                return prop

        return None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ("Device(\t%s,\n\n%s )\n" % (self.ids.string, \
            ",\n\n".join([str(p) for p in self.properties]))) \
            .replace("\n", "\n\t")
