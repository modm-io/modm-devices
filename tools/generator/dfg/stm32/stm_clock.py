# -*- coding: utf-8 -*-
# Copyright (c) 2018, Niklas Hauser
# All rights reserved.

from os.path import commonprefix, basename
import re
import sys
import logging
import subprocess
import tempfile
import textwrap

from collections import defaultdict
from jinja2 import Environment
from pathlib import Path
from ..input.xml import XMLReader

from . import stm

LOGGER = logging.getLogger('dfg.stm32.clock')



class STMClock:
    ROOT_PATH = Path(__file__).parents[2]
    CLOCK_FILE_PATH = ROOT_PATH / "raw-device-data/stm32-devices/plugins/clock"
    CACHE_CLOCK_TREE = {}

    @staticmethod
    def get(did, rcc_ip_file):
        if rcc_ip_file.filename not in STMClock.CACHE_CLOCK_TREE:
            STMClock.CACHE_CLOCK_TREE[rcc_ip_file.filename] = STMClock(did, rcc_ip_file)
        return STMClock.CACHE_CLOCK_TREE[rcc_ip_file.filename]

    def __init__(self, did, rcc_ip_file):
        self.ip_file = rcc_ip_file
        self.did = did

        match = basename(self.ip_file.filename)
        match = re.search(r"RCC-STM32(((..).?.?)E?)[_-]rcc", match)
        ip_name = match.group(1)
        rcc_name = match.group(2)
        family = match.group(3)
        # print(family, rcc_name, ip_name)
        files = [c for c in STMClock.CLOCK_FILE_PATH.glob("*.xml") if str(c).endswith("{}.xml".format(rcc_name))]
        if not files:
            files = [c for c in STMClock.CLOCK_FILE_PATH.glob("*.xml") if rcc_name in str(c)]
        if not files:
            files = [c for c in STMClock.CLOCK_FILE_PATH.glob("*.xml") if str(c).endswith("{}.xml".format(family))]
        if len(files) != 1:
            LOGGER.error("Unknown clock file for device '{}' and IP file '{}': {}".format(did.string, self.ip_file, files))
            return

        self.clock_file = XMLReader(files[0])
        # print(family, files[0])

        self.params = {ref.get("Name"):ref for ref in self.ip_file.query("//RefParameter")}
        self.nodes = {node.get("id"):node for node in self.clock_file.query("//Element")}
        self.signals = {signal.get("id"):signal for signal in self.clock_file.query("//Signal")}
        self.ips = {}
        self.edges = {}
        # ips = {ip.strip():ipn for ipn in self.ip_file.query("//@IP/..") for ip in ipn.get("IP").split(",")}
        # signals = self.clock_file.query("//@signalId")

        for edge in self.clock_file.query("//Input"):
            name = "{}<-{}".format(edge.get("signalId"), edge.get("from"))
            self.edges[name] = edge
        for edge in self.clock_file.query("//Output"):
            name = "{}->{}".format(edge.get("signalId"), edge.get("to"))
            self.edges[name] = edge

        def get_refs(node):
            ref = self.params.get(node.get("refParameter", ""))
            if ref is None: return {};
            attrib = ref.attrib
            if ref.get("Type", "") == "list":
                values = [value.get("Value") for value in ref if value.get("Value") is not None]
                if values:
                    prefix = commonprefix(values)
                    attrib["Values"] = "{}{{{}}}".format(prefix, ",".join(value.replace(prefix, "") for value in values))
            attrib.pop("Visible", None)
            attrib.pop("Display", None)
            attrib.pop("Comment", None)
            attrib.pop("Unit", None)
            attrib.pop("Type", None)
            nmin, ndef, nmax = attrib.pop("Min", ""), attrib.pop("DefaultValue", ""), attrib.pop("Max", "")
            if nmin and nmax and nmin == nmax:
                value = ndef
            else:
                value = ""
                if nmin: value += "{} <= ".format(nmin);
                if ndef: value += "({})".format(ndef);
                if nmax: value += " <= {}".format(nmax);
            attrib["Value"] = value

            return attrib


        import graphviz as gv
        graph = gv.Digraph(format="svg",
                           node_attr={"style": "filled,solid", "shape": "box"})

        for name, node in self.nodes.items():
            refs = get_refs(node)
            label = ["{} {}".format(name, node.get("type", ""))] + ["{}: {}".format(k, v) for k,v in refs.items() if k not in ["IP"]]
            label = [textwrap.fill(l, width=50) for l in label]
            graph.node(name, label="\n".join(label))
            if name == "I2SClockSource":
                print(self.edges.keys())
            if "IP" in refs and not any(edge.startswith("{}->".format(name)) or edge.endswith("<-{}".format(name)) for edge in self.edges.keys()):
                for ip in [ip.strip() for ip in refs["IP"].split(",") if ip.strip()]:
                    self.edges["{}->{}".format(name, ip)] = node
                    graph.node(ip, shape="egg")
                    self.ips[ip] = node

        for name in set(self.signals) - set(self.nodes):
            graph.node(name, shape="pentagon")

        for name, edge in self.edges.items():
            if "->" in name:
                efrom, eto = name.split("->")
            elif "<-" in name:
                eto, efrom = name.split("<-")
            graph.edge(efrom, eto, label=edge.get("refValue", ""))

        outfile = Path("clock/{}.svg".format(ip_name))
        outfile.write_text(graph.pipe().decode("utf-8"))