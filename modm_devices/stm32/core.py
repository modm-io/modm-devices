#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Niklas Hauser
# All rights reserved.

from ..cache import cached_property
from ..driver import Driver
from collections import defaultdict

class DriverCore(Driver):
    def __init__(self, device):
        Driver.__init__(self, device, device._find_first_driver("core"))


    def vectors(self, filterfn=None):
        vecs = (v["name"] for v in self._driver["vector"])
        if filterfn is not None:
            vecs = filter(filterfn, vecs)
        return vecs


    def instance_irq_map(self, name):
        """
        :return: a map from int(instance) to str(name) interrupt starting with {name}.
        """
        vector_map = defaultdict(list)
        for vector in self.vectors(lambda v: v.startswith(name)):
            vrange = sorted(int(d) for d in vector[len(name):].split("_") if d.isdigit())
            if len(vrange) == 2:
                vrange = list(range(vrange[0], vrange[1]+1))
            for num in vrange:
                # if num in vector_map:
                #     raise ValueError("Instance '{}' already in '{}' map!".format(str(num), name))
                vector_map[num].append(vector)
        return vector_map


    def shared_irqs(self, name):
        """
        :return: a map from str(name) to range(instances) >= 2 for interrupts starting with {name}.
        """
        vector_range = {}
        for vector in self.vectors(lambda v: v.startswith(name)):
            vrange = sorted(int(d) for d in vector[len(name):].split("_") if d.isdigit())
            if len(vrange) <= 1:
                continue;
            if len(vrange) == 2:
                vrange = list(range(vrange[0], vrange[1]+1))
            if vector in vector_range:
                raise ValueError("Vector '{}' already in '{}' map!".format(str(vector), name))
            vector_range[vector] = vrange
        return vector_range

