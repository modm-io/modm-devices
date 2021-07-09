# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import os
import re
import logging
from collections import defaultdict

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
    TemperatureMap = {0: "6", 105: "7", 125: "3"}

    @staticmethod
    def _format_raw_devices(rawDevices):
        devices = set()
        for dev in rawDevices:
            temp_max = dev.find("Temperature")
            temp_max = "" if temp_max is None else temp_max.get("Max")
            name = dev.get("RefName")
            temp_max = int(float(temp_max)) if len(temp_max) else min(STMDeviceTree.TemperatureMap)
            for temp, value in STMDeviceTree.TemperatureMap.items():
                if temp_max >= temp:
                    devices.add(name[:12] + value + name[13:])
        return sorted(list(devices))


    @staticmethod
    def getDevicesFromFamily(family):
        devices = STMDeviceTree.familyFile.query('//Family[@Name="{}"]/SubFamily/Mcu/@RefName'.format(family))
        devices = STMDeviceTree._format_raw_devices(devices)
        LOGGER.info("Found devices of family '{}': {}".format(family, ", ".join(devices)))
        return devices

    @staticmethod
    def getDevicesFromPrefix(prefix):
        devices = STMDeviceTree.familyFile.query('//Family/SubFamily/Mcu[starts-with(@RefName,"{}")]'.format(prefix))
        devices = STMDeviceTree._format_raw_devices(devices)
        LOGGER.info("Found devices for prefix '{}': {}".format(prefix, ", ".join(devices)))
        return list(sorted(devices))

    @staticmethod
    def _properties_from_partname(partname):
        deviceNames = STMDeviceTree.familyFile.query('//Family/SubFamily/Mcu[starts-with(@RefName,"{}")]'
                                                     .format(partname[:12] + "x" + partname[13:]))
        comboDeviceName = sorted([d.get("Name") for d in deviceNames])[0]
        device_file = XMLReader(os.path.join(STMDeviceTree.rootpath, comboDeviceName + ".xml"))
        did = STMIdentifier.from_string(partname.lower())
        LOGGER.info("Parsing '{}'".format(did.string))

        # information about the core and architecture
        cores = [c.text.lower().replace("arm ", "") for c in device_file.query('//Core')]
        if len(cores) > 1: did.naming_schema += "@{core}"
        devices = [STMDeviceTree._properties_from_id(comboDeviceName, device_file, did.copy(), c) for c in cores]
        return [d for d in devices if d is not None]

    @staticmethod
    def _properties_from_id(comboDeviceName, device_file, did, core):
        if core.endswith("m4") or core.endswith("m7"):
            core += "f"
        if did.family in ["h7"] or (did.family in ["f7"] and did.name not in ["45", "46", "56"]):
            core += "d"
        if "@" in did.naming_schema:
            did.set("core", core[7:9])
        p = {"id": did, "core": core}

        # Information from the CMSIS headers
        stm_header = STMHeader(did)
        if not stm_header.is_valid:
            LOGGER.error("CMSIS Header invalid for %s", did.string)
            return None

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


        p["ram"] = rams[sizeIndexRam] * 1024
        p["flash"] = flashs[sizeIndexFlash] * 1024

        memories = []
        for (mem_name, mem_start, mem_size) in stm.getMemoryForDevice(did, p["flash"], p["ram"]):
            access = "rwx"
            if did.family == "f4" and mem_name == "ccm": access = "rw";
            if "flash" in mem_name: access = "rx";
            memories.append({"name": mem_name, "access": access, "size": str(mem_size),
                             "start": "0x{:02X}".format(mem_start)})

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
                pass
                # print(version)
            return version

        modules = []
        for ip in device_file.query('//IP'):
            # These IPs are all software modules, NOT hardware modules. Their version string is weird too.
            software_ips = {"GFXSIMULATOR", "GRAPHICS", "FATFS", "TOUCHSENSING", "PDM2PCM",
                            "MBEDTLS", "FREERTOS", "CORTEX_M", "NVIC", "USB_DEVICE",
                            "USB_HOST", "LWIP", "LIBJPEG", "GUI_INTERFACE", "TRACER"}
            if any(ip.get("Name").upper().startswith(p) for p in software_ips):
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

        modules.append( ("flash", "flash", "v1.0"))
        modules = [m + stm_peripherals.getPeripheralData(did, m) for m in modules]

        p["modules"] = modules
        LOGGER.debug("Available Modules are:\n" + STMDeviceTree._modulesToString(modules))
        instances = [m[1] for m in modules]
        # print("\n".join(str(m) for m in modules))

        p["stm_header"] = stm_header
        p["interrupts"] = stm_header.get_interrupt_table()
        # Flash latency table
        p["flash_latency"] = stm.getFlashLatencyForDevice(did)

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
        # Remove package remaps from GPIO data (but not from package)
        pins.sort(key=lambda p: "PINREMAP" not in p.get("Variant", ""))

        gpios = []

        def pin_name(name):
            name = name[:4]
            if len(name) > 3 and not name[3].isdigit():
                name = name[:3]
            return (name[1:2].lower(), name[2:].lower())

        # Find the remap pin pairs, if they exist
        double_pinouts = defaultdict(list)
        for pin in device_file.query('//Pin'):
            double_pinouts[pin.get("Position")].append((pin.get("Name"), pin.get("Variant", "DEFAULT")))
        double_pinouts = {pos: {pin:variant for (pin, variant) in pins}
                                for pos, pins in double_pinouts.items()
                                    if len(pins) > 1 and any("PINREMAP" in pin[1] for pin in pins)}

        # Get the pinout for this package with correct remap variants
        pinout = []
        for pin in device_file.query("//Pin"):
            name = pin.get("Name")
            pos = pin.get("Position")
            pinv = {
                "name": name,
                "position": pos,
                "type": pin.get("Type"),
            }
            variant = double_pinouts.get(pos, {}).get(name)
            if (variant is not None and (pin.get("Type") != "I/O" or (
                pin_name(name)[0] in ['a'] and
                pin_name(name)[1] in ['9', '10', '11', '12']))):
                pinv["variant"] = "remap" if "PINREMAP" in variant else "remap-default"
            pinout.append(pinv)

        p["pinout"] = pinout
        p["package"] = device_file.query("/Mcu/@Package")[0]

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
            af = af.replace("ir_", "irtim_") \
                   .replace("crs_", "rcc_crs_") \
                   .replace("timx_", "tim_")
            if af == "cec": af = "hdmi_cec_cec";

            driver, instance, names = split_af(af)
            rafs = []
            for name in names.split("-"):
                rafs.append( (driver, instance, name) )
            return rafs

        dma_dumped = []
        dma_streams = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        requests = dmaFile.query('//RefParameter[@Name="Request"]/PossibleValue/@Comment')
        if did.family == "h7": requests.insert(54, "Reserved"); # Secret NSA peripheral
        for sig in dmaFile.query('//ModeLogicOperator[@Name="XOR"]/Mode'):
            name = rname = sig.get("Name")
            parent = sig.getparent().getparent().get("Name")
            instance = parent.split("_")[0][3:]
            parent = parent.split("_")[1]

            request = dmaFile.query('//RefMode[@Name="{}"]'.format(name))[0]
            def rv(param, default=[]):
                vls = request.xpath('./Parameter[@Name="{}"]/PossibleValue/text()'.format(param))
                if not len(vls): vls = default;
                return vls

            name = name.lower().split(":")[0]
            if name == "memtomem":
                continue
            # Several corrections
            name = name.replace("spdif_rx", "spdifrx")
            if name.startswith("dac") and "_" not in name: name = "dac_{}".format(name);
            if any(name == n for n in ["sdio", "sdmmc2", "sdmmc1"]): continue
            if len(name.split("_")) < 2: name = "{}_default".format(name);
            driver, inst, name = split_af(name)

            if "[" in parent:
                channel = requests.index(rname)
                stream = instance = 0
                p["dma_naming"] = (None, "request", "signal")
            elif "Stream" in parent:
                channel = rv("Channel", ["software"])[0].replace("DMA_CHANNEL_", "")
                stream = parent.replace("Stream", "")
                p["dma_naming"] = ("stream", "channel", "signal")
            elif rv("Request"):
                channel = rv("Request", ["software"])[0].replace("DMA_REQUEST_", "")
                stream = parent.replace("Channel", "")
                p["dma_naming"] = ("channel", "request", "signal")
            else:
                channel = parent.replace("Channel", "")
                stream = channel
                p["dma_naming"] = (None, "channel", "signal")

            if driver is None: # peripheral is not part of this device
                dma_dumped.append( (instance, stream, name) )
                continue
            mode = [v[4:].lower() for v in rv("Mode")]
            for sname in ([None] if name == "default" else name.split("/")):
                signal = {
                    "driver": driver,
                    "name": sname,
                    "direction": [v[4:].replace("PERIPH", "p").replace("MEMORY", "m").replace("_TO_", "2") for v in rv("Direction")],
                    "mode": mode,
                    "increase": "ENABLE" in rv("PeriphInc", ["DMA_PINC_ENABLE"])[0],
                }
                if inst: signal["instance"] = inst;
                remaps = stm.getDmaRemap(did, instance, channel, driver, inst, sname)
                if remaps: signal["remap"] = remaps;
                dma_streams[instance][stream][channel].append(signal)
                # print(instance, stream, channel)
                # print(signal)

        # Manually handle condition expressions from XML for
        # (STM32F030CCTx|STM32F030RCTx) and (STM32F070CBTx|STM32F070RBTx)
        if did.family in ['f0']:
            if (did.name == '30' and did.size == 'c'):
                dma_streams['1'].pop('6')
                dma_streams['1'].pop('7')
                dma_streams.pop('2')
            if (did.name == '70' and did.size == 'b'):
                dma_streams['1'].pop('6')
                dma_streams['1'].pop('7')

        # De-duplicate DMA signal entries
        def deduplicate_list(l):
            return [i for n, i in enumerate(l) if i not in l[n + 1:]]
        for stream in dma_streams:
            for channel in dma_streams[stream]:
                for signal in dma_streams[stream][channel]:
                    dma_streams[stream][channel][signal] = deduplicate_list(
                        dma_streams[stream][channel][signal])

        # if p["dma_naming"][1] == "request":
        #     print(did, dmaFile.filename)
        p["dma"] = dma_streams
        if len(dma_dumped):
            for instance, stream, name in sorted(dma_dumped):
                LOGGER.debug("DMA{}#{}: dumping {}".format(instance, stream, name))

        # If DMAMUX is used, add DMAMUX to DMA peripheral channel mappings
        if p["dma_naming"] == (None, "request", "signal"):
            # There can be multiple "//RefParameter[@Name="Instance"]" nodes constrained by
            # a <Condition> child node filtering by the STM32 die id
            # Try to match a node with condition first, if nothing matches choose the default one
            die_id = device_file.query('//Die')[0].text
            q = '//RefParameter[@Name="Instance"]/Condition[@Expression="%s"]/../PossibleValue/@Value' % die_id
            channels = dmaFile.query(q)
            if len(channels) == 0:
                # match channels from node without <Condition> child node
                channels = dmaFile.query('//RefParameter[@Name="Instance" and not(Condition)]/PossibleValue/@Value')

            mux_channels = []
            # H7 has "Stream" instead of "Channel" for DMAMUX1
            mux_channel_regex = re.compile(r"DMA(?P<instance>([0-9]))_(Channel|Stream)(?P<channel>([0-9]+))")
            for mux_ch_position, channel in enumerate(channels):
                m = mux_channel_regex.match(channel)
                assert m is not None
                mux_channels.append({'position'     : mux_ch_position,
                                     'dma-instance' : int(m.group("instance")),
                                     'dma-channel'  : int(m.group("channel"))})
            p["dma_mux_channels"] = mux_channels

        if did.family == "f1":
            grouped_f1_signals = gpioFile.compactQuery('//GPIO_Pin/PinSignal/@Name')

        _seen_gpio = set()
        for pin in pins:
            rname = pin.get("Name")
            name = pin_name(rname)

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

            gpio = (name[0], name[1], afs)
            if name not in _seen_gpio:
                gpios.append(gpio)
                _seen_gpio.add(name)
            # print(gpio[0].upper(), gpio[1], afs)
            # LOGGER.debug("{}{}: {} ->".format(gpio[0].upper(), gpio[1]))

        remaps = {}
        if did.family == "f1":
            for remap in gpioFile.compactQuery('//GPIO_Pin/PinSignal/RemapBlock/@Name'):
                module = remap.split("_")[0].lower()
                config = remap.split("_")[1].replace("REMAP", "").replace("IREMAP", "")
                mapping = stm.getGpioRemapForModuleConfig(module, config)

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
                if e["name"] == "dma":
                    # place the dma before the gpio
                    return ("yyyyyyy", e["type"])
                if e["name"] == "gpio":
                    # place the gpio at the very end
                    return ("zzzzzzz", e["type"])
                # sort remaining drivers by type and compatible strings
                return (e["name"], e["type"])
            return ("", "")
        tree.addSortKey(driverOrder)

        core_child = tree.addChild("driver")
        core_child.setAttributes("name", "core")
        if "@" in p["id"].naming_schema:
            type_child = core_child.addChild("attribute-type")
            type_child.setValue(p["core"])
        else:
            core_child.setAttributes("type", p["core"])
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
        for name, hardware, features, protocols, instances in modules.values():
            driver = tree.addChild("driver")
            driver.setAttributes("name", name, "type", hardware)
            if name == "gpio":
                STMDeviceTree.addGpioToNode(p, driver)
                continue

            def driver_sort_key(e):
                if e.name == "feature":
                    return (0, 0, e.get("value", "AAA"))
                if e.name == "instance":
                    if e["value"].isdigit():
                        return (1, int(e["value"]), "")
                    return (1, 0, e["value"])
                return (1e6, 1e6, 1e6)
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
                    iname = i[len(name):]
                    iname = iname.replace("_m", "cortex-m")
                    inst.setValue(iname)

            if name == "flash":
                flv = p["flash_latency"]
                driver.addSortKey(lambda e: int(e.get("vcore-min", 1e6)))
                for mV, freqs in flv.items():
                    vddc = driver.addChild("latency")
                    vddc.setAttributes("vcore-min", mV)
                    vddc.addSortKey(lambda e: (int(e["ws"]), int(e["hclk-max"])))
                    for fi, fmax in enumerate(freqs):
                        fc = vddc.addChild("wait-state")
                        fc.setAttributes("ws", fi, "hclk-max", fmax)


            if name == "dma":
                STMDeviceTree.addDmaToNode(p, driver)

        return tree

    @staticmethod
    def addDmaToNode(p, driver):
        naming = p["dma_naming"]
        driver.addSortKey(lambda e: (int(e.get("instance", 0)), int(e.get("position", 0))))
        for instance, streams in p["dma"].items():
            inst = driver.addChild((naming[1] if naming[0] is None else naming[0]) + "s")
            if naming[0] is not None or naming[1] == "channel":
                inst.setAttribute("instance", instance)
            inst.addSortKey(lambda e: (e.name, int(e["position"])))
            for stream, channels in streams.items():
                if naming[0] is not None:
                    stre = inst.addChild(naming[0])
                    stre.setAttribute("position", stream)
                    stre.addSortKey(lambda e: int(e["position"]))
                else:
                    stre = inst
                for channel, signals in channels.items():
                    chan = stre.addChild(naming[1])
                    chan.setAttribute("position", channel)
                    chan.addSortKey(lambda e: (e["driver"], e.get("instance", ""), e.get("name", "")))
                    for signal in signals:
                        sign = chan.addChild(naming[2])
                        sign.setAttributes(["driver", "instance"], signal)
                        if signal["name"]:
                            sign.setAttributes(["name"], signal)
                        sign.addSortKey(lambda e: (e["position"], e["id"]))
                        for remap in signal.get("remap", []):
                            rem = sign.addChild("remap")
                            rem.setAttributes(["position", "mask", "id"], remap)

        mux_channels = p.get("dma_mux_channels")
        if mux_channels is not None:
            driver_channels = driver.addChild("mux-channels")
            # TODO: attribute "instance" has to be added to mux-channels for H7 BDMA which uses DMAMUX2
            driver_channels.addSortKey(lambda e: (int(e.get("position", 0)),
                                                  int(e.get("dma-instance", 0)),
                                                  int(e.get("dma-channel", 0))))
            for channel in mux_channels:
                chan = driver_channels.addChild("mux-channel")
                chan.setAttributes(["position", "dma-instance", "dma-channel"], channel)

    @staticmethod
    def addGpioToNode(p, gpio_driver):
        if p["id"]["family"] == "f1":
            # Add the remap group tree
            for remap in p["remaps"].values():
                if len(remap["groups"]) == 0: continue;
                remap_ch = gpio_driver.addChild("remap")
                keys = [k for k in ["driver", "instance"] if remap[k] is not None]
                remap_ch.setAttributes(keys + ["position", "mask"], remap)
                remap_ch.addSortKey(lambda e: int(e["id"]))

                for group, pins in remap["groups"].items():
                    group_ch = remap_ch.addChild("group")
                    group_ch.setAttributes("id", group)
                    group_ch.addSortKey(lambda e : (e["port"], int(e["pin"]), e["name"]))

                    for pin in pins:
                        pin_ch = group_ch.addChild("signal")
                        pin_ch.setAttributes(["port", "pin", "name"], pin)

        package = gpio_driver.addChild("package")
        package.setAttributes("name", p["package"])
        def sort_pinout(e):
            alphas = "".join(filter(str.isalpha, e["position"]))
            digits = "".join(filter(str.isdigit, e["position"]))
            return (alphas, int(digits), e.get("variant", ""))
        package.addSortKey(sort_pinout)
        for pin in p["pinout"]:
            pinc = package.addChild("pin")
            pinc.setAttributes(["position", "name"], pin)
            if "I/O" not in pin["type"]:
                pinc.setAttributes("type", pin["type"].lower())
            pinc.setAttributes(["variant"], pin)


        # Sort these things
        def sort_gpios(e):
            if "package" in e.name:
                return (1000, e["name"], 0, "", 0)
            elif "driver" in e:
                return (int(e["position"]), e["driver"], int(e.get("instance", 0)), "", 0)
            else:
                return (100, "", 0, e["port"], int(e["pin"]))
        gpio_driver.addSortKey(sort_gpios)

        for port, pin, signals in p["gpios"]:
            pin_driver = gpio_driver.addChild("gpio")
            pin_driver.setAttributes("port", port, "pin", pin)
            pin_driver.addSortKey(lambda e: (int(e.get("af", -1)),
                                             e.get("driver", ""),
                                             e.get("instance", ""),
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


    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split("-")[-1]
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setAttribute("value", prop)

    @staticmethod
    def addMemoryToNode(p, node):
        for section in p["memories"]:
            memory_section = node.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
        # sort the node children by start address and size
        node.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))

    @staticmethod
    def addInterruptTableToNode(p, node):
        interrupts = p["interrupts"]

        for vector in [i for i in interrupts if i["position"] >= 0]:
            vector_section = node.addChild("vector")
            vector_section.setAttributes(["position", "name"], vector)
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

    @staticmethod
    def from_partname(partname):
        devices = STMDeviceTree._properties_from_partname(partname)
        return [STMDeviceTree._device_tree_from_properties(d) for d in devices]
