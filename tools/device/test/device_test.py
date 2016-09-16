
import unittest

import modm.device

class SelectorTest(unittest.TestCase):

    def test_should_match_an_empty_device(self):
        identifier = modm.device.DeviceIdentifier()
        selector = modm.device.Selector()

        self.assertTrue(selector.match(identifier))

    def test_should_match_property(self):
        identifier = modm.device.DeviceIdentifier()
        identifier.platform = "Test"

        selector = modm.device.Selector()
        selector.property["platform"] = ["Test", "Test1"]

        self.assertTrue(selector.match(identifier))

    def test_should_reject_if_property_set_but_not_in_device(self):
        identifier = modm.device.DeviceIdentifier()
        identifier.platform = "Test"

        selector = modm.device.Selector()
        selector.property["platform"] = ["Test1", "Test2"]

        self.assertFalse(selector.match(identifier))


class MultiDeviceIdentifierTest(unittest.TestCase):

    def test_should_split_into_multiple_devices(self):
        multi = modm.device.MultiDeviceIdentifier()

        multi.name = ("64", "128")
        multi.pin_id = ("", "b3")

        devices = multi.get_devices()

        self.assertEqual(4, len(devices))
