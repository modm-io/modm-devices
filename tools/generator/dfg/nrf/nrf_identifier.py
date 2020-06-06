# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# Copyright (c)      2020, Hannes Ellinger
# All rights reserved.

import re
import logging

from modm_devices.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.nrf.identifier")

class NRFIdentifier:
    """ NRFIdentifier
    A class to parse NRF device strings, e.g. NRF52840-QIAA.
    Device names are organized as follows:
          NRF      52      840  -    QI       AA
      {platform}{family}{series}-{package}{function}
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        if string.startswith("nrf"):
            matchString = r"nrf(?P<family>[0-9]{2})(?P<series>[0-9]{3})-(?P<package>\w{2})(?P<function>\w{2})"
            match = re.search(matchString, string)
            if match:
                i = DeviceIdentifier("{platform}{family}{series}-{package}{function}")
                i.set("platform", "nrf")
                i.set("family", match.group("family").lower())
                i.set("series", match.group("series").lower())
                i.set("package", match.group("package").lower())
                i.set("function", match.group("function").lower())
                return i


        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
