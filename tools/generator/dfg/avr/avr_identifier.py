# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import re
import logging

from modm_devices.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.avr.identifier")

class AVRIdentifier:
    """ AVRIdentifier
    A class to parse AVR device strings, e.g. atmega328p.
    """

    @staticmethod
    def from_string(string):
        string = string.lower()

        # AVR platform with AT90, ATtiny, ATmega and ATxmega family
        if string.startswith("at"):
            matchString = r"at(?P<family>tiny|mega|xmega)(?P<name>\d+)"
            if string.startswith("at90"):
                matchString = r"at(?P<family>90)(?P<type>can|pwm|usb)(?P<name>\d+)-(?P<speed>\d+)(?P<package>\w+)"

            match = re.search(matchString, string)
            if match:
                i = DeviceIdentifier()
                i.set("platform", "avr")
                i.set("family", match.group("family").lower())
                i.set("name", match.group("name").lower())

                if i.family == "90":
                    i.naming_schema = "at{family}{type}{name}-{speed}{package}"
                    i.set("type", match.group("type").lower())
                    i.set("speed", match.group("speed"))
                    i.set("package", match.group("package"))
                    return i

                elif i.family in ["tiny", "mega"]:
                    i.naming_schema = "at{family}{name}{type}-{speed}{package}"
                    searchstr = "at" + i.family + i.name + r"(?P<type>\w*)-(?P<speed>\d*)(?P<package>\w+)"
                    match = re.search(searchstr, string)
                    if match:
                        i.set("type", match.group("type").lower())
                        i.set("speed", match.group("speed"))
                        i.set("package", match.group("package"))
                        return i

                elif i.family == "xmega":
                    i.naming_schema = "at{family}{name}{type}{pin}"
                    searchstr = "at" + i.family + i.name + r"(?P<type>[A-Ea-e]?[1-5]?)(?P<package>[Bb]?[Uu]?)"
                    match = re.search(searchstr, string)
                    if match:
                        if match.group("type") != "":
                            i.set("type", match.group("type").lower())
                        if match.group("package") != "":
                            i.set("pin", match.group("package"))
                    return i

        return None
