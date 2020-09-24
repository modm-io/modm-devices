# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import math
import logging

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .sam_identifier import SAMIdentifier

LOGGER = logging.getLogger("dfg.sam.reader")

class SAMDeviceTree:
    """ SAMDeviceTree
    This SAM specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """

    @staticmethod
    def _devices_from_file(filename):
        device_file = XMLReader(filename)
        devices = device_file.query("//variants/variant/@ordercode")
        return list(set(d for d in devices if d != "standard"))

    @staticmethod
    def _properties_from_file(filename, devname):
        p = {}

        device_file = XMLReader(filename)
        device = device_file.query("//device")[0]
        variant = device_file.query(f'//variants/variant[@ordercode="{devname}"]')[0]
        did = SAMIdentifier.from_string(devname.lower())
        p["id"] = did

        LOGGER.info("Parsing '%s'", did.string)

        # Package information
        p["package"] = variant.get("package")
        p["pinout"] = variant.get("pinout")
        p["pinout_pins"] = {
            p.get("position"): p.get("pad")
            for p in device_file.query(f'//pinouts/pinout[@name="{p["pinout"]}"]/pin')
        }

        # information about the core and architecture
        core = device_file.query("//device")[0].get("architecture").lower().replace("plus", "+")
        for param in (device_file.query("//device/parameters")[0]):
            if param.get("name") == "__FPU_PRESENT" and param.get("value") == "1":
                core += "f"
        p["core"] = core

        # find the values for flash, ram and (optional) eeprom
        memories = []
        for memory_segment in device_file.query("//memory-segment"):
            memType = memory_segment.get("type")
            name = memory_segment.get("name")
            start = memory_segment.get("start")
            size = int(memory_segment.get("size"), 16)
            access = memory_segment.get("rw").lower()
            if memory_segment.get("exec") == "true":
                access += "x"
            if name in ["FLASH"]:
                memories.append({"name":"flash", "access":"rx", "size":str(size), "start":start})
            elif name in ["HMCRAMC0", "HMCRAM0", "HSRAM"]:
                memories.append({"name":"ram", "access":access, "size":str(size), "start":start})
            elif name in ["LPRAM", "BKUPRAM"]:
                memories.append({"name":"lpram", "access":access, "size":str(size), "start":start})
            elif name in ["SEEPROM", "RWW"]:
                memories.append({"name":"eeprom", "access":"r", "size":str(size), "start":start})
            elif name in ["QSPI"]:
                memories.append({"name":"extram", "access":access, "size":str(size), "start":start})
            else:
                LOGGER.debug("Memory segment '%s' not used", name)
        p["memories"] = memories

        raw_modules = device_file.query("//peripherals/module/instance")
        modules = []
        ports = []
        for m in raw_modules:
            tmp = {"module": m.getparent().get("name").lower(), "instance": m.get("name").lower()}
            if tmp["module"] == "port":
                ports.append(tmp)
            else:
                modules.append(tmp)
        p["modules"] = sorted(list(set([(m["module"], m["instance"]) for m in modules])))

        signals = []
        gpios = []
        raw_signals = device_file.query("//peripherals/module/instance/signals/signal")
        for s in raw_signals:
            tmp = {"module": s.getparent().getparent().getparent().get("name").lower(),
                    "instance": s.getparent().getparent().get("name").lower()}
            tmp.update({k:v.lower() for k,v in s.items()})
            if tmp["group"] in ["p", "pin"] or tmp["group"].startswith("port"):
                gpios.append(tmp)
            else:
                signals.append(tmp)
        gpios = sorted([(g["pad"][1], g["pad"][2:]) for g in gpios])

        p["signals"] = signals
        # Filter gpios by pinout
        p["gpios"] = [pin for pin in gpios if f"P{pin[0].upper()}{pin[1]}" in p["pinout_pins"].values()]

        interrupts = []
        for i in device_file.query("//interrupts/interrupt"):
            interrupts.append({"position": i.get("index"), "name": i.get("name")})
        p["interrupts"] = interrupts

        #### Events are similar to interrupts, but instead of triggering an ISR data is passed from source
        #### to sink without waking the processor
        # event sources
        event_sources = []
        for i in device_file.query("//events/generators/generator"):
            event_sources.append({"index": i.get("index"), "name": i.get("name"), "instance": i.get("module-instance")})
        p["event_sources"] = event_sources

        # event sinks or "users" as the datasheet calls them
        event_users = []
        for i in device_file.query("//events/users/user"):
            event_users.append({"index": i.get("index"), "name": i.get("name"), "instance": i.get("module-instance")})
        p["event_users"] = event_users

        LOGGER.debug("Found GPIOs: [%s]", ", ".join([p.upper() + i for p,i in p["gpios"]]))
        LOGGER.debug("Available Modules are:\n" + SAMDeviceTree._modulesToString(p["modules"]))
        # LOGGER.debug("Found Signals:")
        # for sig in p["signals"]:
        #     LOGGER.debug("    %s", sig)
        # LOGGER.debug("Found Interrupts:")
        # for intr in p["interrupts"]:
        #     LOGGER.debug("    %s", intr)
        # LOGGER.debug("Found Event Sources:")
        # for eventSrc in p["event_sources"]:
        #     LOGGER.debug("    %s", eventSrc)
        # LOGGER.debug("Found Event Users:")
        # for eventUsr in p["event_users"]:
        #     LOGGER.debug("    %s", eventUsr)

        return p

    @staticmethod
    def _modulesToString(modules):
        string = ""
        mods = sorted(modules)
        char = mods[0][0][0:1]
        for module, instance in mods:
            if not instance.startswith(char):
                string += "\n"
            string += instance + " \t"
            char = instance[0][0:1]
        return string

    @staticmethod
    def _device_tree_from_properties(p):
        tree = DeviceTree("device")
        tree.ids.append(p["id"])

        def topLevelOrder(e):
            order = ["attribute-flash", "attribute-ram", "attribute-eeprom", "attribute-core", "attribute-mcu", "header", "attribute-define"]
            if e.name in order:
                if e.name in ["attribute-flash", "attribute-eeprom", "attribute-ram"]:
                    return (order.index(e.name), int(e["value"]))
                else:
                    return (order.index(e.name), e["value"])
            return (len(order), -1)
        # tree.addSortKey(topLevelOrder)

        # SAMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-flash")
        # SAMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-ram")
        # SAMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-eeprom")
        # SAMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-mcu")

        def driverOrder(e):
            if e.name == "driver":
                if e["name"] == "core":
                    # place the core at the very beginning
                    return ("aaaaaaa", e["type"])
                if e["name"] == "gpio":
                    # place the gpio at the very end
                    return ("zzzzzzz", e["type"])
                # sort remaining drivers by type and compatible strings
                return (e["name"], e["type"])
            return ("", "")
        tree.addSortKey(driverOrder)

        # Core
        core_child = tree.addChild("driver")
        core_child.setAttributes("name", "core", "type", p["core"])
        core_child.addSortKey(lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, ""))
        core_child.addSortKey(lambda e: (e["name"], int(e["size"])) if e.name == "memory" else ("", -1))

        for section in p["memories"]:
            memory_section = core_child.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
        # sort the node children by start address and size
        core_child.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))

        # for memory in ["flash", "ram", "lpram", "eeprom"]:
        #     if memory not in p: continue;
        #     memory_section = core_child.addChild("memory")
        #     memory_section.setAttribute("name", memory)
        #     memory_section.setAttribute("size", p[memory])

        for vector in p["interrupts"]:
            if int(vector["position"]) < 0: continue;
            vector_section = core_child.addChild("vector")
            vector_section.setAttributes(["position", "name"], vector)

        modules = {}
        for m, i in p["modules"]:
            # filter out non-peripherals: fuses, micro-trace buffer
            if m in ["fuses", "mtb", "systemcontrol", "systick", "hmatrixb", "hmatrix"]: continue;
            if m not in modules:
                modules[m] = [i]
            else:
                modules[m].append(i)

        # add all other modules
        for name, instances in modules.items():
            driver = tree.addChild("driver")
            dtype = name
            compatible = "sam"

            driver.setAttributes("name", dtype, "type", compatible)
            # Add all instances to this driver
            if any(i != dtype for i in instances):
                driver.addSortKey(lambda e: e["value"])
                for i in instances:
                    inst = driver.addChild("instance")
                    inst.setValue(i[len(dtype):])

        # GPIO driver
        gpio_driver = tree.addChild("driver")
        gpio_driver.setAttributes("name", "gpio", "type", "sam")
        gpio_driver.addSortKey(lambda e : (e["port"], int(e["pin"])))
        for port, pin in p["gpios"]:
            pin_driver = gpio_driver.addChild("gpio")
            pin_driver.setAttributes("port", port.upper(), "pin", pin)
            pin_driver.addSortKey(lambda e: (e["driver"],
                                             e["instance"] if e["instance"] is not None else "",
                                             e["name"] if e["name"] is not None else ""))
            # add all signals
            for s in [s for s in p["signals"] if s["pad"] == ("p" + port + pin)]:
                driver, instance, name = s["module"], s["instance"], s["group"]
                # add the af node
                pin_signal = {"driver": driver, "function": s["function"]}
                if "index" in s:
                    pin_signal["index"] = s["index"]
                if instance != driver:
                    pin_signal["instance"] = instance.replace(driver, "")
                if name != driver and name != "int":
                    pin_signal["name"] = name
                elif "index" in s:
                    pin_signal["name"] = s["index"]
                if "name" not in pin_signal:
                    LOGGER.error("%s has no name!", s)
                    continue
                af = pin_driver.addChild("signal")
                af.setAttributes(["driver", "instance", "name", "function", "index"], pin_signal)

        return tree

    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split("-")[-1]
        if pname not in p: return;
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setValue(prop)

    @staticmethod
    def from_file(filename):
        devices = []
        for name in SAMDeviceTree._devices_from_file(filename):
            p = SAMDeviceTree._properties_from_file(filename, name)
            if p is None: continue;
            devices.append(SAMDeviceTree._device_tree_from_properties(p))
        return devices
