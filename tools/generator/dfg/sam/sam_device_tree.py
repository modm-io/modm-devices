# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# Copyright (c)      2022, Christopher Durand
# All rights reserved.

import math
import logging
import re

from collections import defaultdict

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
            access = memory_segment.get("rw", "r").lower()
            if memory_segment.get("exec") == "true":
                access += "x"
            if name in ["FLASH", "IFLASH"]:
                memories.append({"name":"flash", "access":"rx", "size":str(size), "start":start})
            elif name in ["HMCRAMC0", "HMCRAM0", "HSRAM", "IRAM"]:
                memories.append({"name":"ram", "access":access, "size":str(size), "start":start})
            elif name in ["LPRAM", "BKUPRAM"]:
                memories.append({"name":"lpram", "access":access, "size":str(size), "start":start})
            elif name in ["SEEPROM", "RWW"]:
                memories.append({"name":"eeprom", "access":"r", "size":str(size), "start":start})
            else:
                LOGGER.debug("Memory segment '%s' not used", name)
        p["memories"] = memories

        raw_modules = device_file.query("//peripherals/module/instance")
        modules = []
        ports = []
        p["gclk_data"] = {}
        p["gclk_data"]["clocks"] = defaultdict(list)
        p["dma_requests"] = defaultdict(list)
        for m in raw_modules:
            module_name = m.getparent().get("name").lower()
            instance = m.get("name").lower()
            tmp = {"module": module_name, "instance": instance}
            parameters = {}
            for param in m.xpath("parameters/param"):
                name = param.get("name")
                if name.startswith("GCLK_ID"):
                    clock_name = name[8:].lower()
                    clock_info = (clock_name if clock_name != "" else None, param.get("value"))
                    p["gclk_data"]["clocks"][instance].append(clock_info)
                if name.startswith("DMAC_ID_"):
                    signal = "_".join(name.lower().split("_")[2:])
                    request_id = int(param.get("value"))
                    p["dma_requests"][instance].append((signal, request_id))

            if module_name == "gclk":
                p["gclk_data"]["generator_count"] = int(m.xpath('parameters/param[@name="GEN_NUM"]')[0].attrib["value"])
            if module_name == "port":
                ports.append(tmp)
            else:
                modules.append(tmp)
        p["modules"] = sorted(list(set([(m["module"], m["instance"]) for m in modules])))

        # parse GCLK sources from register section
        generators = device_file.query('//modules/module[@name="GCLK"]/value-group[@name="GCLK_GENCTRL__SRC"]/value')
        p["gclk_data"]["sources"] = dict([(g.get("name").capitalize(), g.get("value")) for g in generators])

        signals = []
        gpios = []
        raw_signals = device_file.query("//peripherals/module/instance/signals/signal")
        for s in raw_signals:
            tmp = {"module": s.getparent().getparent().getparent().get("name").lower(),
                    "instance": s.getparent().getparent().get("name").lower()}
            tmp.update({k:v.lower() for k,v in s.items()})

            # Fix duplicate GPIO data for SAMx7x revision A devices
            if did.family == "E7x/S7x/V7x" and did.variant == "a":
                if tmp["module"] in ("sdramc", "smc"):
                    continue

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

        def driver_compatibility(id):
            s = id.string
            # TODO: do we really need this distinction?
            # There are two groups of devices with common peripherals:
            # - SAM x7x,G5x
            # - SAM D09,D1x,D2x,L2x,D51,E5x
            # TODO: What would be the appropriate naming for those groups?
            if s.startswith("samg5"):
                return "samg"
            else:
                return "sam"

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

        compatible = driver_compatibility(p['id'])

        # add all other modules
        instance_pattern = re.compile(r"^(?P<per>([a-z0-9]*[a-z]+))(?P<instance>([0-9]+))$")
        for name, instances in modules.items():
            driver = tree.addChild("driver")
            dtype = name

            driver.setAttributes("name", dtype, "type", compatible)
            # Add all instances to this driver
            if any(i != dtype for i in instances):
                driver.addSortKey(lambda e: e["value"])
                for i in instances:
                    inst = driver.addChild("instance")
                    inst.setValue(i[len(dtype):])
            if name == "gclk":
                driver.addSortKey(lambda e: (e.name, int(e["value"]), e.get("peripheral", ""), e.get("instance", ""), e.get("name", "")))
                for instance, instance_clocks in p["gclk_data"]["clocks"].items():
                    for clock_info in instance_clocks:
                        clock = driver.addChild("clock")
                        clock_name, clock_id = clock_info
                        m = instance_pattern.match(instance)
                        if m:
                            clock.setAttributes("peripheral", m.group("per"), "instance", m.group("instance"))
                        else:
                            clock.setAttributes("peripheral", instance)
                        if clock_name is not None:
                            clock.setAttribute("name", clock_name)
                        clock.setAttribute("value", clock_id)
                for name, source_id in p["gclk_data"]["sources"].items():
                    source = driver.addChild("source")
                    source.setAttributes("name", name, "value", source_id)
                generators = driver.addChild("generators")
                generators.setAttributes("value", str(p["gclk_data"]["generator_count"]))
            # Add request data to DMA module
            # Skip D09 devices, information is missing in raw data.
            elif name in ("dmac", "xdmac", "pdc") and p["id"].series != "d09":
                driver.addSortKey(lambda e: (int(e["id"]), e["peripheral"], e.get("instance", ""), e["signal"]))
                for instance, request_list in p["dma_requests"].items():
                    for signal, request_id in request_list:
                        req = driver.addChild("request")
                        m = instance_pattern.match(instance)
                        if m:
                            req.setAttributes("peripheral", m.group("per"), "instance", m.group("instance"))
                        else:
                            req.setAttributes("peripheral", instance)
                        req.setAttributes("signal", signal, "id", request_id)

        # GPIO driver
        gpio_driver = tree.addChild("driver")
        gpio_driver.setAttributes("name", "gpio", "type", compatible)
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
