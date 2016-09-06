
import unittest

import modm.device

class DeviceTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_should_match_an_empty_device(self):
        device = modm.device.Device()
        selector = modm.device.Selector()
        
        self.assertTrue(selector.match(device))
    
    def test_should_match_property(self):
        device = modm.device.Device()
        device.platform = "Test"
        
        selector = modm.device.Selector()
        selector.property["platform"] = ["Test", "Test1"]
        
        self.assertTrue(selector.match(device))
    
    def test_should_reject_if_property_set_but_not_in_device(self):
        device = modm.device.Device()
        device.platform = "Test"
        
        selector = modm.device.Selector()
        selector.property["platform"] = ["Test1", "Test2"]
        
        self.assertFalse(selector.match(device))
