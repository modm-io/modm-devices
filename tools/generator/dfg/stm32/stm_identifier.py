# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import re
import logging

from modm.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.stm.identifier")

class STMIdentifier:
    """ STMIdentifier
    A class to parse STM device strings, e.g. "stm32f407vg".
    """
    @staticmethod
    def from_string(string):
        i = DeviceIdentifier()
        string = string.lower()

        if string.startswith("stm32"):
            i.naming_schema = "{platform}{family}{name}{pin}{size}{package}"
            i.set("platform", "stm32")
            i.set("family", string[5:7])
            i.set("name", string[7:9])
            if len(string) >= 10:
                i.set("pin", string[9])
            if len(string) >= 11:
                i.set("size", string[10])
            if len(string) >= 12:
                i.set("package", string[11])
            return i

        LOGGER.error("Parse Error: unknown platform. Device string: %s", string)
        exit(1)
