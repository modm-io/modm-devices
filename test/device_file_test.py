
import unittest
import glob
import os

import modm_devices.parser

DEVICE_FILES = None

class DeviceFileTest(unittest.TestCase):

    def setUp(self):
        global DEVICE_FILES
        if DEVICE_FILES is None:
            DEVICE_FILES = {}
            device_files = os.path.join(os.path.dirname(__file__), "../devices/**/*.xml")
            # device_files = os.path.join(os.path.dirname(__file__), "../devices/stm32/stm32l1-51_52_62-c_d_e.xml")
            device_file_names  = glob.glob(device_files)

            # Parse the files and build the :target enumeration
            parser = modm_devices.parser.DeviceParser()
            for device_file_name in device_file_names:
                for device in parser.parse(device_file_name).get_devices():
                    DEVICE_FILES[device.partname] = device

        # self.devices = {"stm32l152vdt6": DEVICE_FILES["stm32l152vdt6"]}
        self.devices = DEVICE_FILES


    def tearDown(self):
        self.devices = None

    def get_drivers(self, device):
        drivers = []
        for d in device._properties["driver"]:
            if "instance" in d:
                drivers.extend( (d["name"], i["name"]) for i in d["instance"] )
            else:
                drivers.append( (d["name"],) )
        return drivers

    def test_drivers(self):
        failures = 0
        for name, device in self.devices.items():
            def assertIn(key, obj):
                if key not in obj:
                    print('{}: Missing "{}" key in "{}"!'.format(name, key, obj))
                    nonlocal failures
                    failures += 1
                    return False
                return True
            drivers = self.get_drivers(device)
            gpios = device.get_driver("gpio")
            assertIn("gpio", gpios)
            for gpio in gpios.get("gpio", []):
                signals = []
                for signal in gpio.get("signal", []):
                    # Check for name and driver keys in each signal
                    assertIn("name", signal)
                    if assertIn("driver", signal):
                        # Check if the signal driver is known
                        if "instance" in signal:
                            driver = (signal["driver"], signal["instance"])
                        else:
                            driver = (signal["driver"],)
                        signals.append( (*driver, signal["name"]) )
                        # assertIn(driver, drivers)

                # Check for duplicate signals
                if not len(signals) == len(set(signals)):
                    duplicates = set(x for x in signals if signals.count(x) > 1)
                    print("{}: duplicated signals for P{}{}: {}".format(
                            name, gpio["port"].upper(), gpio["pin"], duplicates))
                    failures += 1
                    # print(gpio)

        # self.assertEqual(failures, 0, "Found inconsistencies in the device files!")







