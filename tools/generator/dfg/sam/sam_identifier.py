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
          SAM     D21     E    15       A    -    M       U
      {platform}{series}{pin}{flash}{variant}-{package}{grade}
    """

    @staticmethod
    def family_from_series(series):
        if series[0] == "c" and series[1] == "2":
            return "C2x"
        elif series[0] == "d":
            if series[1] == "5":
                return "D5x/E5x"
            elif series[1] in ("0", "1", "2", "a"):
                return "D1x/D2x/DAx"
        elif series[0] == "e" and series[1] == "5":
            return "D5x/E5x"
        elif series[0] == "g" and series[1] == "5":
            return "G5x"
        elif series[0] == "l":
            if series[1] == "1":
                return "L1x"
            elif series[1] == "2":
                return "L2x"
        elif series[0] in ("e", "s", "v") and series[1] == "7":
            return "E7x/S7x/V7x"
        elif series[0] == "4":
            return "4"
        raise ValueError("Unsupported SAM series '{}'".format(series))

    @staticmethod
    def from_string(string):
        string = string.lower()

        # SAM platform with SAMD, SAML, SAMC, SAM4, SAMG, SAMS, SAME, and SAMV
        if string.startswith("sam") or string.startswith("atsam"):
            if string.startswith("atsam4"):
                matchString = r"sam(?P<series>\d\w)(?P<flash>\d{1,2})(?P<pin>\w)(?P<variant>\w)?-(?P<package>\w)(?P<grade>\w)"
            else:
                matchString = r"sam(?P<series>\w((\d{2})|(\w\d)))(?P<pin>\w)(?P<flash>\d{2})(?P<variant>\w)?-(?P<package>\w\w*)(?P<grade>\w)$"
            match = re.search(matchString, string.lower())
            if match:
                i = DeviceIdentifier("{platform}{series}{pin}{flash}{variant}-{package}{grade}")
                i.set("platform", "sam")
                i.set("series", match.group("series"))
                i.set("pin", match.group("pin"))
                i.set("flash", match.group("flash"))

                i.set("variant", match.group("variant") or "")
                i.set("package", match.group("package"))
                i.set("grade", match.group("grade"))

                i.set("family", SAMIdentifier.family_from_series(match.group("series")).lower())
                return i

        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
