
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


def id_from_string(string):
    i = DeviceIdentifier("{platform}{family}{name}{pin}{size}{package}{temperature}{variant}")
    i.set("platform", string[:5])
    i.set("family", string[5:7])
    i.set("name", string[7:9])
    i.set("pin", string[9])
    i.set("size", string[10])
    i.set("package", string[11])
    i.set("temperature", string[12])
    if len(string) >= 14:
        i.set("variant", string[13])
    else:
        i.set("variant", "")
    return i


class MultiDeviceIdentifierTest(unittest.TestCase):

    def setUp(self):
        self.ident = MultiDeviceIdentifier()
        self.devices = MultiDeviceIdentifier(list(map(id_from_string, [
            "stm32l151cct6",
            "stm32l151cct7",
            "stm32l151ccu6",
            "stm32l151ccu7",
            "stm32l151qch6",
            "stm32l151qdh6",
            "stm32l151qeh6",
            "stm32l151rct6",
            "stm32l151rct6a",
            "stm32l151rcy6",
            "stm32l151rdt6",
            "stm32l151rdt7",
            "stm32l151rdy6",
            "stm32l151rdy7",
            "stm32l151ret6",
            "stm32l151ucy6",
            "stm32l151ucy7",
            "stm32l151vch6",
            "stm32l151vct6",
            "stm32l151vct6a",
            "stm32l151vdt6",
            "stm32l151vdt6x",
            "stm32l151vdy6x",
            "stm32l151vdy7x",
            "stm32l151vet6",
            "stm32l151vet7",
            "stm32l151vey6",
            "stm32l151vey7",
            "stm32l151zct6",
            "stm32l151zdt6",
            "stm32l151zet6",
            "stm32l152cct6",
            "stm32l152ccu6",
            "stm32l152qch6",
            "stm32l152qdh6",
            "stm32l152qeh6",
            "stm32l152rct6",
            "stm32l152rct6a",
            "stm32l152rdt6",
            "stm32l152rdy6",
            "stm32l152ret6",
            "stm32l152ucy6",
            "stm32l152vch6",
            "stm32l152vct6",
            "stm32l152vct6a",
            "stm32l152vdt6",
            "stm32l152vdt6x",
            "stm32l152vet6",
            "stm32l152vey6",
            "stm32l152zct6",
            "stm32l152zdt6",
            "stm32l152zet6",
            "stm32l162qdh6",
            "stm32l162rct6",
            "stm32l162rct6a",
            "stm32l162rdt6",
            "stm32l162rdy6",
            "stm32l162ret6",
            "stm32l162vch6",
            "stm32l162vct6",
            "stm32l162vct6a",
            "stm32l162vdt6",
            "stm32l162vdy6x",
            "stm32l162vet6",
            "stm32l162vey6",
            "stm32l162zdt6",
            "stm32l162zet6"
        ])))
        self.child_devices = MultiDeviceIdentifier(list(map(id_from_string, [
            "stm32l152qch6",
            "stm32l152qdh6",
            "stm32l152qeh6",
            "stm32l152vch6",
            "stm32l152rct6a",
            "stm32l152rdt6",
            "stm32l152ret6",
            "stm32l152vct6a",
            "stm32l152vct6",
            "stm32l152vdt6x",
            "stm32l152vdt6",
            "stm32l152vet6",
            "stm32l152zct6",
            "stm32l152zdt6",
            "stm32l152zet6",
            "stm32l152rdy6",
            "stm32l152vey6",
            "stm32l162qdh6",
            "stm32l162vch6",
            "stm32l162rct6a",
            "stm32l162rdt6",
            "stm32l162ret6",
            "stm32l162vct6a",
            "stm32l162vct6",
            "stm32l162vdt6",
            "stm32l162vet6",
            "stm32l162zdt6",
            "stm32l162zet6",
            "stm32l162rdy6",
            "stm32l162vdy6x",
            "stm32l162vey6",
        ])))
        self.parent_devices = MultiDeviceIdentifier(list(map(id_from_string, [
            "stm32l151qch6",
            "stm32l151qdh6",
            "stm32l151qeh6",
            "stm32l151vch6",
            "stm32l151rct6a",
            "stm32l151rct6",
            "stm32l151rdt6",
            "stm32l151rdt7",
            "stm32l151ret6",
            "stm32l151vct6a",
            "stm32l151vct6",
            "stm32l151vdt6x",
            "stm32l151vdt6",
            "stm32l151vet6",
            "stm32l151vet7",
            "stm32l151zct6",
            "stm32l151zdt6",
            "stm32l151zet6",
            "stm32l151rcy6",
            "stm32l151rdy6",
            "stm32l151rdy7",
            "stm32l151ucy6",
            "stm32l151ucy7",
            "stm32l151vdy6x",
            "stm32l151vdy7x",
            "stm32l151vey6",
            "stm32l151vey7",
            "stm32l152qch6",
            "stm32l152qdh6",
            "stm32l152qeh6",
            "stm32l152vch6",
            "stm32l152rct6a",
            "stm32l152rct6",
            "stm32l152rdt6",
            "stm32l152ret6",
            "stm32l152vct6a",
            "stm32l152vct6",
            "stm32l152vdt6x",
            "stm32l152vdt6",
            "stm32l152vet6",
            "stm32l152zct6",
            "stm32l152zdt6",
            "stm32l152zet6",
            "stm32l152rdy6",
            "stm32l152ucy6",
            "stm32l152vey6",
            "stm32l162qdh6",
            "stm32l162vch6",
            "stm32l162rct6a",
            "stm32l162rct6",
            "stm32l162rdt6",
            "stm32l162ret6",
            "stm32l162vct6a",
            "stm32l162vct6",
            "stm32l162vdt6",
            "stm32l162vet6",
            "stm32l162zdt6",
            "stm32l162zet6",
            "stm32l162rdy6",
            "stm32l162vdy6x",
            "stm32l162vey6",
        ])))

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

    # def test_minimal_subtract_set(self):
    #     print(self.devices)
    #     print(self.parent_devices)
    #     print(self.child_devices)

    #     min_set = self.child_devices.minimal_subtract_set(self.devices, self.parent_devices)
    #     for m in min_set:
    #         print([(k, m.getAttribute(k)) for k in self.devices.keys() if m.getAttribute(k)])
    #     self.assertEqual(min_set, "[f1]")
