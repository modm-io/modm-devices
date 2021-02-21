#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Niklas Hauser
# All rights reserved.

from collections import defaultdict
from ..cache import *
from ..access import copy_keys, copy_deep
from ..driver import Driver

class DriverGpio(Driver):
    def __init__(self, device):
        Driver.__init__(self, device, device._find_first_driver("gpio"))

    @cached_property
    def ranges(self):
        """
        Computes all port ranges on this device in the form of a map:

        - "name": port.upper()
        - "start": min(pin)
        - "width": max(pin) - min(pin)

        :return: a list of port ranges
        """
        ports = defaultdict(list)
        for gpio in self._driver["gpio"]:
            ports[gpio["port"]].append(int(gpio["pin"]))

        ports = [{"name": k,
                  "start": min(v),
                  "width": max(v) - min(v) + 1}  for k,v in ports.items()]
        ports.sort(key=lambda p: p["name"])
        return ports

    @cached_property
    def ports(self):
        """
        Computes all ports on this device.

        :return: a sorted unique list of ports in uppercase letters.
        """
        ports = set(p["port"] for p in self._driver["gpio"])
        return list(sorted(ports))

    @cached_property
    def pins(self):
        """
        Computes all pins on this device.

        :return: a sorted unique list of (port.upper(), int(pin)) tuples.
        """
        pins = set((p["port"], int(p["pin"])) for p in self._driver["gpio"])
        return list(sorted(pins))

    def signals(self, port, pin):
        return self._signals.get((port.lower(), pin))

    # @cached_function
    def signals_by_name(self, port, pin):
        signals = self.signals(port, pin)
        names = defaultdict(list)
        for s in signals:
            names[s["name"]].append(s)
        return dict(names)

    @cached_property
    def signals_remap(self):
        return copy_deep(self._driver.get("remap", []))

    @cached_property
    def package_remap(self):
        # Compute the set of remapped pins
        remapped_gpios = {}
        for p in self._driver["package"][0]["pin"]:
            variant = p.get("variant", "")
            if "remap" in variant:  # also matches "remap-default"
                name = p["name"][1:4].strip().lower()
                if len(name) > 2 and not name[2].isdigit():
                    name = name[:2]
                remapped_gpios[name] = (variant == "remap") # "remap-default" -> False
        return remapped_gpios

    @cached_property
    def signals_group(self):
        sgroup = defaultdict(list)
        if "f1" in self.type:
            # Convert the map from a list of signals to a list of pins
            for remap in self._driver["remap"]:
                for group in remap["group"]:
                    for signal in group["signal"]:
                        key = (signal["port"], int(signal["pin"]))

                        for sig in sgroup[key]:
                            if ((sig["driver"], sig.get("instance", 0)) ==
                                    (remap["driver"], int(remap.get("instance", 0))) and
                                    sig["name"] == signal["name"]):
                                sig["group"].append(int(group["id"]))
                                break
                        else:
                            sig = copy_keys(remap, "driver", ("instance", int))
                            sig["name"] = signal["name"]
                            sig["group"]= [int(group["id"])]
                            sgroup[key].append(sig)
        return dict(sgroup)


    @cached_property
    def signals_all(self):
        asigs = list()
        for signals in self._signals.values():
            for s in signals:
                asigs.append(copy_keys(s, "name", "driver", ("instance", int)))
        return asigs

    @cached_property
    def _signals(self):
        """
        :return:
        """
        signals_map = {}
        for gpio in self._driver["gpio"]:
            key = (gpio["port"], int(gpio["pin"]))

            raw_signals = copy_deep(gpio.get("signal", []))
            # raw_signals = gpio.get("signal", [])
            if key in self.signals_group:
                raw_signals.extend(self.signals_group[key])

            for s in raw_signals:
                s.update(copy_keys(s, ("af", int), ("instance", int)))
                s["is_analog"] = any(s.get("driver", "").startswith(p) for p in {"adc", "dac", "comp"})
                if s.get("driver", "").startswith("adc") and s["name"].startswith("in"):
                    s["analog_channel"] = int("".join(filter(str.isdigit, s["name"])))

            signals_map[key] = raw_signals

        # print(signals_map)
        return signals_map


