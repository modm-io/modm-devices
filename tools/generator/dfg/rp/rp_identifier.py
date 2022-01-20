# -*- coding: utf-8 -*-
# Copyright (c) 2022, Andrey Kunitsyn
# All rights reserved.

import re
import logging

from modm_devices.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.rp.identifier")

class RPIdentifier:
    """ RPIdentifier
    A class to parse RP device strings, e.g. RP2040.
    Device names are organized as follows:
          RP      2      0    4    0
      {platform}{cores}{type}{ram}{flash}
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        if string.startswith("rp"):
            i = DeviceIdentifier("{platform}{cores}{type}{ram}{flash}")
            i.set("platform", "rp")
            i.set("cores", string[2])
            i.set("type", string[3])
            i.set("ram", string[4])
            i.set("flash", string[5])
            i.set("family", string[2:4])
            return i



        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
