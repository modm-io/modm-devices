#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# All rights reserved.

import unittest

import modm.name
import modm.device

class NameTest(unittest.TestCase):

    def test_should_parse_schema_string(self):
        schema_string = "at{{ family }}{{ name }}{{ type }}{{ pin_id }}"
        schema = modm.name.Schema.parse(schema_string)
        self.assertEqual(5, len(schema.parts))

        self.assertEqual("at", schema.parts[0].name)
        self.assertEqual("family", schema.parts[1].name)
        self.assertEqual("name", schema.parts[2].name)
        self.assertEqual("type", schema.parts[3].name)
        self.assertEqual("pin_id", schema.parts[4].name)

    def test_should_parse_schema_string_with_fixed_part_first(self):
        schema_string = "{{ platform }}f{{ name }}{{ pin_id }}{{ size_id }}"
        schema = modm.name.Schema.parse(schema_string)
        self.assertEqual(5, len(schema.parts))

    def test_should_create_name(self):
        identifier = modm.device.DeviceIdentifier()
        identifier.platform = "stm32"
        identifier.name = "407"
        identifier.pin_id = "v"
        identifier.size_id = "g"

        schema_string = "{{ platform }}f{{ name }}{{ pin_id }}{{ size_id }}"
        schema = modm.name.Schema.parse(schema_string)

        self.assertEqual("stm32f407vg", schema.get_name(identifier))

    def test_should_extract_attributes_from_schema(self):
        schema_string = "{{ platform }}f{{ name }}{{ pin_id }}{{ size_id }}"
        schema = modm.name.Schema.parse(schema_string)

        self.assertListEqual(["platform", "name", "pin_id", "size_id"], schema.get_attributes())
