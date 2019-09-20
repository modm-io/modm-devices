# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import re
import logging

from modm_devices.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.stm.identifier")

class STMIdentifier:
    """ STMIdentifier
    A class to parse STM device strings, e.g. "stm32f407vg".
    """
    @staticmethod
    def from_string(string):
        string = string.lower()

        if string.startswith("stm32"):
            i = DeviceIdentifier("{platform}{family}{name}{pin}{size}{package}{temperature}{variant}")
            i.set("platform", "stm32")
            i.set("family", string[5:7])
            i.set("name", string[7:9])
            i.set("pin", string[9])
            i.set("size", string[10])
            i.set("package", string[11])
            i.set("temperature", string[12])
            if len(string) >= 14:
                i.set("variant", string[13])
            else:
                i.set("variant", "")
            return i

        LOGGER.error("Parse Error: unknown platform. Device string: %s", string)
        exit(1)
