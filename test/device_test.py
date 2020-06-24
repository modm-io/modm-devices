
import unittest

from modm_devices.exception import DeviceIdentifierException
from modm_devices.device_identifier import DeviceIdentifier, MultiDeviceIdentifier

class DeviceIdentifierTest(unittest.TestCase):

    def test_should_construct_empty(self):
        ident = DeviceIdentifier()
        self.assertEqual(repr(ident), "DeviceId()")
        self.assertEqual(len(ident.keys()), 0)
        self.assertRaises(DeviceIdentifierException,
                          lambda: ident.string)
        self.assertRaises(DeviceIdentifierException,
                          lambda: str(ident))
        self.assertRaises(AttributeError,
                          lambda: ident.whatevs)


    def test_setter_getter(self):
        ident = DeviceIdentifier()
        ident.set("platform", "stm32")
        self.assertEqual(ident.get("platform"), "stm32")
        self.assertEqual(ident["platform"], "stm32")
        self.assertEqual(ident.platform, "stm32")
        self.assertEqual(repr(ident), "DeviceId(platformstm32)")
        self.assertRaises(DeviceIdentifierException,
                          lambda: ident.string)
        self.assertRaises(DeviceIdentifierException,
                          lambda: str(ident))

        ident.set("platform", "avr")
        self.assertEqual(ident.get("platform"), "avr")
        self.assertEqual(ident["platform"], "avr")
        self.assertEqual(ident.platform, "avr")

        self.assertEqual(ident.get("whatevs"), None)
        self.assertEqual(ident.get("whatevs", "default"), "default")
        self.assertEqual(ident["whatevs"], None)
        self.assertRaises(AttributeError,
                          lambda: ident.whatevs)


    def test_naming_schema(self):
        ident = DeviceIdentifier("{platform}{family}{name}")
        self.assertEqual(ident.string, "")
        ident.set("platform", "stm32")
        self.assertEqual(ident.string, "stm32")
        ident.set("name", "03")
        self.assertEqual(ident.string, "stm3203")
        ident.set("family", "f1")
        self.assertEqual(ident.string, "stm32f103")

        self.assertEqual(str(ident), "stm32f103")
        self.assertEqual(repr(ident), "stm32f103")
        self.assertEqual(hash(ident), hash("familyf1name03platformstm32{platform}{family}{name}"))

        ident2 = DeviceIdentifier("{platform}{family}{name}")
        ident2.set("platform", "stm32")
        ident2.set("family", "f1")
        ident2.set("name", "03")
        self.assertEqual(hash(ident2), hash("familyf1name03platformstm32{platform}{family}{name}"))

        self.assertTrue(ident == ident2)
        self.assertFalse(ident != ident2)
        self.assertEqual(ident, ident2)

        ident3 = DeviceIdentifier("{platform}{family}")
        ident3.set("platform", "stm32")
        ident3.set("family", "f1")
        self.assertEqual(hash(ident3), hash("familyf1platformstm32{platform}{family}"))

        self.assertTrue(ident != ident3)
        self.assertFalse(ident == ident3)
        self.assertNotEqual(ident, ident3)


    def test_copy(self):
        ident = DeviceIdentifier("{platform}")
        ident.set("platform", "stm32")

        ident2 = ident.copy()
        self.assertEqual(ident2.platform, "stm32")
        self.assertEqual(ident2.naming_schema, "{platform}")
        ident2.set("platform", "avr")
        self.assertEqual(ident2.platform, "avr")
        self.assertEqual(ident.platform, "stm32")
        ident2.naming_schema = "{platform}{family}"
        self.assertEqual(ident2.naming_schema, "{platform}{family}")
        self.assertEqual(ident.naming_schema, "{platform}")



class MultiDeviceIdentifierTest(unittest.TestCase):

    def setUp(self):
        self.ident = MultiDeviceIdentifier()

    def test_should_construct_empty(self):
        self.assertEqual(self.ident.string, "")
        self.assertEqual(self.ident.naming_schema, "")

    def test_should_merge_naming_schemas(self):

        self.ident.append(DeviceIdentifier("{one}"))
        self.assertEqual(self.ident.naming_schema, "{one}")

        self.ident.append(DeviceIdentifier("{one}"))
        self.assertEqual(self.ident.naming_schema, "{one}")

        self.ident.append(DeviceIdentifier("{one}{two}"))
        self.assertEqual(self.ident.naming_schema, "{one}{one}{two}")
