# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import re
import logging

from modm_devices.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.sam.identifier")

class SAMIdentifier:
    """ SAMIdentifier
    A class to parse SAM device strings, e.g. ATSAMD21E15A-MUT.
    Device names are organized as follows:
          SAM       D      21     E    15       A    -    M
      {platform}{family}{series}{pin}{flash}{variant}{package}
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        # SAM platform with SAMD, SAML, SAMC, SAM4, SAMG, SAMS, SAME, and SAMV
        if string.startswith("sam") or string.startswith("atsam"):
            matchString = r"a?t?sam(?P<family>[a-z])(?P<series>[0-9]{2})(?P<pin>[a-z])(?P<flash>[0-9]{2})(?P<variant>[a-z])(?P<package>u?)"
            match = re.search(matchString, string)
            if match:
                i = DeviceIdentifier("{platform}{family}{series}{pin}{flash}{variant}{package}")
                i.set("platform", "sam")
                i.set("family", match.group("family").lower())
                i.set("series", match.group("series").lower())
                i.set("pin", match.group("pin").lower())
                i.set("flash", match.group("flash").lower())
                i.set("variant", match.group("variant").lower())
                # package in atdf file is either U (wlcsp) or not annotated.
                # we will use 'm' (normally QFN) to represent all other options (TQFP, UFBGA)
                if match.group("package"):
                    i.set("package", match.group("package").lower())
                else:
                    i.set("package", 'm')
                return i
                

        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
