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
       ATSAMD     21         E        15        A     -    M          U           T
      {family} {Series} {Pin Count} {Flash} {Revision} {pacakge} {Temp Grade} {carrier}
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        # SAM platform with SAMD, SAML, SAMC, SAM4, SAMG, SAMS, SAME, and SAMV
        if string.lower().startswith("atsam"):
            # revision is the silicon revision of the chip
            matchString = r"ATSAM(?P<family>[A-Z])(?P<name>[0-9]{2})(?P<pin>.)(?P<size>[0-9]{2})(?P<revision>.+)\."
            match = re.search(matchString, string)
            if match:
                i = DeviceIdentifier()
                i.set("platform", "sam")
                i.set("family", match.group("family").lower())
                i.set("name", match.group("name").lower())
                i.set("pin", match.group("pin").lower())
                i.set("size", match.group("size").lower())
                i.set("revision", match.group("revision").lower())

        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
