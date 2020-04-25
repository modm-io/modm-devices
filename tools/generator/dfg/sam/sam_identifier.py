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
          SAM       D      21     E    15       A    -    M       U
      {platform}{family}{series}{pin}{flash}{variant}-{package}{grade}
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        # SAM platform with SAMD, SAML, SAMC, SAM4, SAMG, SAMS, SAME, and SAMV
        if string.startswith("sam") or string.startswith("atsam"):
            matchString = r"sam(?P<family>\w)(?P<series>\d{2})(?P<pin>\w)(?P<flash>\d{2})(?P<variant>\w)-(?P<package>\w)(?P<grade>\w)"
            match = re.search(matchString, string.lower())
            if match:
                i = DeviceIdentifier("{platform}{family}{series}{pin}{flash}{variant}-{package}{grade}")
                i.set("platform", "sam")
                i.set("family", match.group("family"))
                i.set("series", match.group("series"))
                i.set("pin", match.group("pin"))
                i.set("flash", match.group("flash"))
                i.set("variant", match.group("variant"))
                i.set("package", match.group("package"))
                i.set("grade", match.group("grade"))
                return i

        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
