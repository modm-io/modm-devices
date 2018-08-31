# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import re
import logging

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .stm_header import STMHeader
from .stm_identifier import STMIdentifier
from . import stm
from . import stm_peripherals

LOGGER = logging.getLogger("dfg.stm.reader")

class STMDeviceTree:
    """ STMDeviceTree
    This STM specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """
    rootpath = os.path.join(os.path.dirname(__file__), "..", "..", "raw-device-data", "stm32-devices", "mcu")
    familyFile = XMLReader(os.path.join(rootpath, "families.xml"))

    @staticmethod
    def getDevicesFromFamily(family):
        rawDevices = STMDeviceTree.familyFile.query('//Family[@Name="{}"]/SubFamily/Mcu/@RefName'.format(family))
        devices = []
        for dev in sorted(rawDevices):
            if len(dev) >= 14: continue;
            shortDev = dev[:12]
            if all(not d.startswith(shortDev) for d in devices):
                devices.append(shortDev)

        LOGGER.info("Found devices of family '{}': {}".format(family, ", ".join(devices)))
        return devices

    @staticmethod
    def getDevicesFromPrefix(prefix):
        rawDevices = STMDeviceTree.familyFile.query('//Family/SubFamily/Mcu/@RefName')
        devices = []
        for dev in sorted(rawDevices):
            if len(dev) >= 14 or not dev.startswith(prefix): continue;
            shortDev = dev[:12]
            if all(not d.startswith(shortDev) for d in devices):
                devices.append(shortDev)

        LOGGER.info("Found devices for prefix '{}': {}".format(prefix, ", ".join(devices)))
        return devices

    @staticmethod
    def _properties_from_partname(partname):
        p = {}

        deviceNames = STMDeviceTree.familyFile.query('//Family/SubFamily/Mcu[starts-with(@RefName,"{}")]'.format(partname))
        comboDeviceName = sorted([d.get("Name") for d in deviceNames])[0]
        device_file = XMLReader(os.path.join(STMDeviceTree.rootpath, comboDeviceName + ".xml"))
        did = STMIdentifier.from_string(partname.lower())
        p["id"] = did

        LOGGER.info("Parsing '{}'".format(did.string))

        # information about the core and architecture
        core = device_file.query('//Core')[0].text.replace("ARM ", "").lower()
        if core.endswith("m4") or core.endswith("m7"):
            core += "f"
        if did.family in ["h7"] or (did.family in ["f7"] and did.name not in ["45", "46", "56"]):
            core += "d"
        p["core"] = core

        # flash and ram sizes
        # The <ram> and <flash> can occur multiple times.
        # they are "ordered" in the same way as the `(S-I-Z-E)` ids in the device combo name
        # we must first find out which index the current did.size has inside `(S-I-Z-E)`
        sizeIndexFlash = 0
        sizeIndexRam = 0

        match = re.search(r"\(.(-.)*\)", comboDeviceName)
        if match:
            sizeArray = match.group(0)[1:-1].lower().split("-")
            sizeIndexFlash = sizeArray.index(did.size)
            sizeIndexRam = sizeIndexFlash

        rams = sorted([int(r.text) for r in device_file.query('//Ram')])
        if sizeIndexRam >= len(rams):
            sizeIndexRam = len(rams) - 1

        flashs = sorted([int(f.text) for f in device_file.query('//Flash')])
        if sizeIndexFlash >= len(flashs):
            sizeIndexFlash = len(flashs) - 1



        if did.family in ["h7"]:
            memories = [
                {"name": "sram",   "access": "rwx", "start": "0x24000000", "size": str(512*1024)},
                {"name": "sram1",  "access": "rwx", "start": "0x30000000", "size": str(128*1024)},
                {"name": "sram2",  "access": "rwx", "start": "0x30020000", "size": str(128*1024)},
                {"name": "sram3",  "access": "rwx", "start": "0x30040000", "size":  str(32*1024)},
                {"name": "sram4",  "access": "rwx", "start": "0x38000000", "size":  str(64*1024)},
                {"name": "backup", "access": "rwx", "start": "0x38800000", "size":   str(4*1024)},
                {"name": "itcm",   "access": "rwx", "start": "0x00000000", "size":  str(64*1024)},
                {"name": "dtcm",   "access": "rx",  "start": "0x20000000", "size": str(128*1024)},
                {"name": "flash",  "access": "rx",  "start": "0x08000000", "size": flashs[sizeIndexFlash]*1024},
            ]
        else:
            mem_start, mem_model = stm.getMemoryForDevice(did)
            total_ram = ram = rams[sizeIndexRam] * 1024 + mem_model["sram1"]
            flash = flashs[sizeIndexFlash] * 1024 + mem_model["flash"]
            if "ccm" in mem_model:
                total_ram += mem_model["ccm"]
            if "backup" in mem_model:
                total_ram += mem_model["backup"]
            if "itcm" in mem_model:
                total_ram += mem_model["itcm"]
                total_ram += mem_model["dtcm"]

            p["ram"] = total_ram
            p["flash"] = flash

            # first get the real SRAM1 size
            for mem, val in mem_model.items():
                if any(s in mem for s in ["2", "3"]):
                    ram -= val

            memories = []
            # add all memories
            for mem, val in mem_model.items():
                if "1" in mem:
                    memories.append({"name": "sram1", "access" : "rwx", "size": str(ram),
                                     "start": "0x{:02X}".format(mem_start["sram" if "sram" in mem_start else "sram1"])})
                elif "2" in mem:
                    memories.append({"name": "sram2", "access" : "rwx", "size": str(val),
                                     "start": "0x{:02X}".format((mem_start["sram"] + ram) if "sram" in mem_start else mem_start["sram2"])})
                elif "3" in mem:
                    memories.append({"name": "sram3", "access": "rwx", "size": str(val),
                                     "start": "0x{:02X}".format(mem_start["sram"] + ram + mem_model["sram2"])})
                elif "flash" in mem:
                    memories.append({"name": "flash", "access": "rx", "size": str(flash),
                                     "start": "0x{:02X}".format(mem_start["flash"])})
                else:
                    memories.append({"name": mem, "size": str(val),
                                     "access": "rw" if did.family == "f4" and mem == "ccm" else "rwx",
                                     "start": "0x{:02X}".format(mem_start[mem])})

        p["memories"] = memories

        # packaging
        package = device_file.query('//@Package')[0]
        p["pin-count"] = re.findall(r"[0-9]+", package)[0]
        p["package"] = re.findall(r"[A-Za-z\.]+", package)[0]

        def clean_up_version(version):
            match = re.search("v[1-9]_[0-9x]", version.replace(".", "_"))
            if match:
                version = match.group(0).replace("_", ".")
            else:
                print(version)
            return version

        modules = []
        for ip in device_file.query('//IP'):
            # These IPs are all software modules, NOT hardware modules. Their version string is weird too.
            if ip.get("Name").upper() in ["GFXSIMULATOR", "GRAPHICS", "FATFS", "TOUCHSENSING", "PDM2PCM", "MBEDTLS", "FREERTOS", "CORTEX_M7", "NVIC", "USB_DEVICE", "USB_HOST", "LWIP", "LIBJPEG"]:
                continue

            rversion = ip.get("Version")
            module = (ip.get("Name"), ip.get("InstanceName"), clean_up_version(rversion))

            if module[0] == "DMA":
                # lets load additional information about the DMA
                dmaFile = XMLReader(os.path.join(STMDeviceTree.rootpath, "IP", "DMA-" + rversion + "_Modes.xml"))
                for rdma in dmaFile.query('//IP/ModeLogicOperator/Mode[starts-with(@Name,"DMA")]/@Name'):
                    for dma in rdma.split(","):
                        modules.append((module[0].lower(), dma.strip().lower(), module[2].lower()))
                continue
            if module[0].startswith("TIM"):
                module = ("TIM",) + module[1:]

            modules.append(tuple([m.lower() for m in module]))

        modules = [m + stm_peripherals.getPeripheralData(did, m) for m in modules]

        p["modules"] = modules
        LOGGER.debug("Available Modules are:\n" + STMDeviceTree._modulesToString(modules))
        instances = [m[1] for m in modules]
        # print("\n".join(str(m) for m in modules))

        # Information from the CMSIS headers
        stm_header = STMHeader(did)
        p["stm_header"] = stm_header
        p["interrupts"] = stm_header.get_interrupt_table()

        # lets load additional information about the GPIO IP
        ip_file = device_file.query('//IP[@Name="GPIO"]')[0].get("Version")
        ip_file = os.path.join(STMDeviceTree.rootpath, "IP", "GPIO-" + ip_file + "_Modes.xml")
        gpioFile = XMLReader(ip_file)

        pins = device_file.query('//Pin[@Type="I/O"][starts-with(@Name,"P")]')
        def raw_pin_sort(p):
            port = p.get("Name")[1:2]
            pin = p.get("Name")[:4]
            if len(pin) > 3 and not pin[3].isdigit():
                pin = pin[:3]
            return (port, int(pin[2:]))
        pins = sorted(pins, key=raw_pin_sort)

        gpios = []

        def split_af(af):
            # entry 0 contains names without instance
            # entry 1 contains names with instance
            mdriv = [m for m in modules if af.startswith(m[0] + "_")]
            minst = [m for m in modules if af.startswith(m[1] + "_")]
            # print(af, mdriv, minst)
            if len(minst) > 1:
                LOGGER.warning("Ambiguos driver: {} {}".format(af, minst))
                exit(1)

            minst = minst[0] if len(minst) else None
            mdriv = mdriv[0] if len(mdriv) else None

            driver = minst[0] if minst else (mdriv[0] if mdriv else None)
            if not driver:
                LOGGER.debug("Unknown driver: {}".format(af))
            instance = None
            if minst and driver:
                pinst = minst[1].replace(driver, "")
                if len(pinst): instance = pinst;
            if minst or mdriv:
                name = af.replace((minst[1] if minst else mdriv[0]) + "_", "")
                if not len(name):
                    LOGGER.error("Unknown name: {} {}".format(af, minst, mdriv))
                    exit(1)
            else:
                name = af

            return (driver, instance, name)

        def split_multi_af(af):
            driver, instance, names = split_af(af)
            rafs = []
            for name in names.split("-"):
                rafs.append( (driver, instance, name) )
            return rafs

        if did.family == "f1":
            grouped_f1_signals = gpioFile.compactQuery('//GPIO_Pin/PinSignal/@Name')

        for pin in pins:
            rname = pin.get("Name")
            name = rname[:4]
            if len(name) > 3 and not name[3].isdigit():
                name = name[:3]

            # the analog channels are only available in the Mcu file, not the GPIO file
            localSignals = device_file.compactQuery('//Pin[@Name="{}"]/Signal[not(@Name="GPIO")]/@Name'.format(rname))
            # print(name, localSignals)
            altFunctions = []

            if did.family == "f1":
                altFunctions = [ (s.lower(), "-1") for s in localSignals if s not in grouped_f1_signals]
            else:
                allSignals = gpioFile.compactQuery('//GPIO_Pin[@Name="{}"]/PinSignal/SpecificParameter[@Name="GPIO_AF"]/..'.format(rname))
                signalMap = { a.get("Name"): a[0][0].text.lower().replace("gpio_af", "")[:2].replace("_", "") for a in allSignals }
                altFunctions = [ (s.lower(), (signalMap[s] if s in signalMap else "-1")) for s in localSignals ]

            afs = []
            for af in altFunctions:
                for raf in split_multi_af(af[0]):
                    naf = {}
                    naf["driver"], naf["instance"], naf["name"] = raf
                    naf["af"] = af[1] if int(af[1]) >= 0 else None
                    if "exti" in naf["name"]: continue;
                    afs.append(naf)

            gpio = (name[1:2].lower(), name[2:].lower(), afs)
            gpios.append(gpio)
            # print(gpio[0].upper(), gpio[1], afs)
            # LOGGER.debug("{}{}: {} ->".format(gpio[0].upper(), gpio[1]))

        remaps = {}
        if did.family == "f1":
            for remap in gpioFile.compactQuery('//GPIO_Pin/PinSignal/RemapBlock/@Name'):
                module = remap.split("_")[0].lower()
                config = remap.split("_")[1].replace("REMAP", "").replace("IREMAP", "")
                mapping = stm.getRemapForModuleConfig(module, config)

                mpins = []
                for pin in gpioFile.compactQuery('//GPIO_Pin/PinSignal/RemapBlock[@Name="{}"]/..'.format(remap)):
                    name = pin.getparent().get("Name")[:4].split("-")[0].split("/")[0].strip().lower()
                    pport, ppin = name[1:2], name[2:]
                    if not any([pp[0] == pport and pp[1] == ppin for pp in gpios]):
                        continue
                    mmm = {"port": pport, "pin": ppin}
                    driver, _, name = split_af(pin.get("Name").lower())
                    if driver is None: continue;
                    mmm["name"] = name;
                    mpins.append(mmm)

                if module not in remaps:
                    driver, instance, _ = split_af(module + "_lol")
                    if not driver: continue;
                    remaps[module] = {
                        "mask": mapping["mask"],
                        "position": mapping["position"],
                        "groups": {},
                        "driver": driver,
                        "instance": instance,
                    }
                if len(mpins) > 0:
                    remaps[module]["groups"][mapping["mapping"]] = mpins
                    LOGGER.debug("{:<20}{}".format(module + "_" + config, ["{}{}:{}".format(b["port"], b["pin"], b["name"]) for b in mpins]))

            # import json
            # print(json.dumps(remaps, indent=4))

        p["remaps"] = remaps
        p["gpios"] = gpios

        return p

    @staticmethod
    def _modulesToString(modules):
        string = ""
        mods = sorted(modules)
        char = mods[0][0][0:1]
        for _, instance, _, _, _, _ in mods:
            if not instance.startswith(char):
                string += "\n"
            string += instance + " \t"
            char = instance[0][0:1]
        return string

    @staticmethod
    def _device_tree_from_properties(p):
        tree = DeviceTree("device")
        tree.ids.append(p["id"])
        LOGGER.info("Generating Device Tree for '{}'".format(p["id"].string))

        # def topLevelOrder(e):
        #     order = ["attribute-flash", "attribute-ram", "attribute-core", "header", "attribute-define"]
        #     if e.name in order:
        #         if e.name in ["attribute-flash", "attribute-ram"]:
        #             return (order.index(e.name), int(e["value"]))
        #         else:
        #             return (order.index(e.name), e["value"])
        #     return (len(order), -1)
        # tree.addSortKey(topLevelOrder)

        # STMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-flash")
        # STMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-ram")
        # STMDeviceTree.addDeviceAttributesToNode(p, tree, "attribute-pin-count")

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

        core_child = tree.addChild("driver")
        core_child.setAttributes("name", "core", "type", p["core"])
        # Memories
        STMDeviceTree.addMemoryToNode(p, core_child)
        STMDeviceTree.addInterruptTableToNode(p, core_child)

        modules = {}
        for m, i, _, h, f, pr in p["modules"]:
            # if m in ["fatfs", "freertos"]: continue;
            if m+h not in modules:
                modules[m+h] = (m, h, f, pr, [i])
            else:
                if (modules[m+h][1] != h):
                    print(modules[m+h], "<-", (m, h, f, pr, i))
                modules[m+h][4].append(i)

        # add all other modules
        gpio_version = "stm32"
        for name, hardware, features, protocols, instances in modules.values():
            if name == "gpio":
                gpio_version = hardware
                continue

            driver = tree.addChild("driver")
            driver.setAttributes("name", name, "type", hardware)
            def driver_sort_key(e):
                if e.name == "feature":
                    return (0, 0, e["value"])
                return (1, int(e["value"]), "")
            driver.addSortKey(driver_sort_key)
            for f in features:
                feat = driver.addChild("feature")
                feat.setValue(f)
            # for pr in protocols:
            #     prot = driver.addChild("protocol")
            #     prot.setValue(pr)
            # Add all instances to this driver
            if any(i != name for i in instances):
                for i in instances:
                    inst = driver.addChild("instance")
                    inst.setValue(i[len(name):])

        # GPIO driver
        gpio_driver = tree.addChild("driver")
        gpio_driver.setAttributes("name", "gpio", "type", gpio_version)

        if p["id"]["family"] == "f1":
            # Add the remap group tree
            for remap in p["remaps"].values():
                if len(remap["groups"]) == 0: continue;
                remap_ch = gpio_driver.addChild("remap")
                if remap["driver"] is not None:
                    remap_ch.setAttributes(["driver"], remap)
                if remap["instance"] is not None:
                    remap_ch.setAttributes(["instance"], remap)
                remap_ch.setAttributes(["position", "mask"], remap)
                remap_ch.addSortKey(lambda e: int(e["id"]))

                for group, pins in remap["groups"].items():
                    group_ch = remap_ch.addChild("group")
                    group_ch.setAttributes("id", group)
                    group_ch.addSortKey(lambda e : (e["port"], int(e["pin"]), e["name"]))

                    for pin in pins:
                        pin_ch = group_ch.addChild("signal")
                        pin_ch.setAttributes(["port", "pin", "name"], pin)

        # Sort these things
        def sort_gpios(e):
            if e["driver"] is None:
                return (100, "", 0, e["port"], int(e["pin"]))
            else:
                return (int(e["position"]), e["driver"], int(0 if e["instance"] is None else e["instance"]), "", 0)
        gpio_driver.addSortKey(sort_gpios)

        for port, pin, signals in p["gpios"]:
            pin_driver = gpio_driver.addChild("gpio")
            pin_driver.setAttributes("port", port, "pin", pin)
            pin_driver.addSortKey(lambda e: (int(e["af"]) if e["af"] is not None else -1,
                                             e["driver"] if e["driver"] is not None else "",
                                             e["instance"] if e["instance"] is not None else "",
                                             e["name"]))
            # add all signals
            for s in signals:
                afid, driver, instance, name = s["af"], s["driver"], s["instance"], s["name"]
                # if driver.startswith("tc"): driver = "tc";
                # if driver == "cpu": driver = "core"; instance = "core";
                # add the af node
                af = pin_driver.addChild("signal")
                if afid == "": LOGGER.error("afid is not set: {}".format(s));
                if afid:     af.setAttributes("af", afid);
                if driver:   af.setAttributes("driver", driver);
                if instance: af.setAttributes("instance", instance);
                af.setAttributes("name", name)

        return tree


    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split("-")[-1]
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setAttribute("value", prop)
            child.setIdentifier(lambda e: e.name)

    @staticmethod
    def addMemoryToNode(p, node):
        for section in p["memories"]:
            memory_section = node.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
            memory_section.setIdentifier(lambda e: e["name"])
        # sort the node children by start address and size
        node.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))

    @staticmethod
    def addInterruptTableToNode(p, node):
        interrupts = p["interrupts"]

        for vector in [i for i in interrupts if i["position"] >= 0]:
            vector_section = node.addChild("vector")
            vector_section.setAttributes(["position", "name"], vector)
            vector_section.setIdentifier(lambda e: e["position"])
        # sort the node children by vector number and name
        node.addSortKey(lambda e: (int(e["position"]), e["name"]) if e.name == "vector" else (-1, ""))

    @staticmethod
    def addModuleAttributesToNode(p, node, peripheral, name, family="stm32"):
        modules = p["modules"]

        peripherals = []
        if isinstance(peripheral, list):
            peripherals.extend(peripheral)
        else:
            peripherals.append(peripheral)

        driver = node.addChild("driver")
        driver.setAttributes("name", name, "family", family)
        driver.addSortKey(lambda e: int(e["value"]))
        driver.setIdentifier(lambda e: e["name"] + e["hw"])

        for module in modules:
            instances = []
            found = False
            for p in peripherals:
                if module.startswith(p):
                    found = True
                    inst = module[len(p):]
                    if inst != "" and inst.isdigit():
                        instances.append(inst)

            if not found:
                continue
            for instance in instances:
                child = driver.addChild("instance")
                child.setAttribute("value", instance)
                child.setIdentifier(lambda e: e.name)

    @staticmethod
    def from_partname(partname):
        p = STMDeviceTree._properties_from_partname(partname)
        if p is None: return None;
        return STMDeviceTree._device_tree_from_properties(p)
