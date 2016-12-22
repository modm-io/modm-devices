# -*- coding: utf-8 -*-
# Copyright (c) 2013     , Kevin Läufer
# Copyright (c) 2013-2014, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import re
import logging

from modm.device_identifier import DeviceIdentifier

LOGGER = logging.getLogger("dfg.avr.identifier")

class AVRIdentifier:
    """ AVRIdentifier
    A class to parse AVR device strings, e.g. atmega328p.
    """

    @staticmethod
    def from_string(string):
        i = DeviceIdentifier()
        string = string.lower()

        # AVR platform with AT90, ATtiny, ATmega and ATxmega family
        if string.startswith("at"):
            i["platform"] = "avr"
            matchString = "at(?P<family>tiny|mega|xmega)(?P<name>\d+)"
            if string.startswith("at90"):
                matchString = "at(?P<family>90)(?P<type>can|pwm|usb)(?P<name>\d+)"
            match = re.search(matchString, string)
            if match:
                i["family"] = match.group("family").lower()
                i["name"] = match.group("name").lower()
                i["type"] = ""

                if i["family"] == "90":
                    i.naming_schema = "at{family}{type}{name}"
                    i["type"] = match.group("type").lower()
                    return i
                elif i["family"] in ["tiny", "mega"]:
                    i.naming_schema = "at{family}{name}{type}"
                    searchstr = "at" + i["family"] + i["name"] + "(?P<type>\w*)-?(?P<package>\w*)"
                    match = re.search(searchstr, string)
                    if match:
                        if match.group("type") != "":
                            i["type"] = match.group("type").lower()
                        if match.group("package") != "":
                            i["pin"] = match.group("package").lower()
                            i.naming_schema = i.naming_schema + "-{pin}"
                        return i

                elif i["family"] == "xmega":
                    i.naming_schema = "at{family}{name}{type}{pin}"
                    i["pin"] = ""
                    searchstr = "at" + i["family"] + i["name"] + "(?P<type>[A-Ea-e]?[1-5]?)(?P<package>[Bb]?[Uu]?)"
                    match = re.search(searchstr, string)
                    if match:
                        if match.group("type") != "":
                            i["type"] = match.group("type").lower()
                        if match.group("package") != "":
                            i["pin"] = match.group("package")
                    return i

        LOGGER.error("Parse Error: unknown platform. Device string: '%s'", string)
        exit(1)
