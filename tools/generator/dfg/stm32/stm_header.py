# -*- coding: utf-8 -*-
# Copyright (c) 2018, Niklas Hauser
# All rights reserved.

import re
import sys
import logging
import subprocess
import tempfile

from collections import defaultdict
from jinja2 import Environment
from pathlib import Path

from ..input.cmsis_header import CmsisHeader
import json

from . import stm

LOGGER = logging.getLogger('dfg.stm32.cmsis.header')

HEADER_TEMPLATE = \
r"""
#include <iostream>
#include <{{header}}>

template<typename T>
void __modm_dump_f(char const *symbol, T value) {
    std::cout << "\"" << symbol << "\": " << uint64_t(value) << "," << std::endl;
}
#define __modm_dump(def) __modm_dump_f(#def, (def))
int main() {
    std::cout << "cpp_defines = {";{% for define in defines %}
#ifdef {{define}}
    __modm_dump({{define}});
#endif{% endfor %}
    std::cout << "}";
    return 0;
}
"""

class STMHeader:
    ROOT_PATH = Path(__file__).parents[2]
    HEADER_PATH = ROOT_PATH / "ext/cmsis-header-stm32"
    CMSIS_PATH =  ROOT_PATH / "ext/cmsis-5-partial/CMSIS/Core/Include"
    CACHE_PATH =  ROOT_PATH / "cmsis-header-cache"
    CACHE_HEADER = defaultdict(dict)
    CACHE_FAMILY = defaultdict(dict)
    BUILTINS = {
        "const uint32_t": 4,
        "const uint16_t": 2,
        "const uint8_t": 1,
        "uint32_t": 4,
        "uint16_t": 2,
        "uint8_t":  1,
    }

    def __init__(self, did):
        self.did = did
        self.family_folder = "stm32{}xx".format(self.did.family)
        self.cmsis_folder = STMHeader.HEADER_PATH / self.family_folder / "Include"
        self.family_header_file = "{}.h".format(self.family_folder)

        self.family_defines = self._get_family_defines()
        self.define = stm.getDefineForDevice(self.did, self.family_defines)
        self.is_valid = self.define is not None
        if not self.is_valid: return;

        self.header_file = "{}.h".format(self.define.lower())
        self.device_map = None

        if self.header_file not in STMHeader.CACHE_HEADER:
            replace_patterns = [
                (r"/\* +?Legacy defines +?\*/.*?\n\n", ""),
                (r"/\* +?Legacy aliases +?\*/.*?\n\n", ""),
                (r"/\* +?Old .*? legacy purpose +?\*/.*?\n\n", ""),
                (r"/\* +?Aliases for .*? +?\*/.*?\n\n", ""),
                # (r"( 0x[0-9A-F]+)\)                 ", "$1U"),
                # (r"#define.*?/\*!<.*? Legacy .*?\*/\n", ""),
            ]
            STMHeader.CACHE_HEADER[self.header_file]["header"] = CmsisHeader.get_header(self.cmsis_folder / self.header_file, replace_patterns)
        self.header = STMHeader.CACHE_HEADER[self.header_file]["header"]

    def get_defines(self):
        if "defines" not in STMHeader.CACHE_HEADER[self.header_file]:
            STMHeader.CACHE_HEADER[self.header_file]["defines"] = self._get_defines()
        return STMHeader.CACHE_HEADER[self.header_file]["defines"]

    def get_memory_map(self):
        if "memmap" not in STMHeader.CACHE_HEADER[self.header_file]:
            STMHeader.CACHE_HEADER[self.header_file]["memmap"] = self._get_memmap()
        return STMHeader.CACHE_HEADER[self.header_file]["memmap"]


    def get_interrupt_table(self):
        if "vectors" not in STMHeader.CACHE_HEADER[self.header_file]:
            interrupt_enum = [i["values"] for i in self.header.enums if i["name"] == 'IRQn_Type'][0]
            vectors = [{"position": int(str(i["value"]).replace(" ", "")),
                        "name": i["name"][:-5]} for i in interrupt_enum]
            STMHeader.CACHE_HEADER[self.header_file]["vectors"] = vectors
        return STMHeader.CACHE_HEADER[self.header_file]["vectors"]


    def _get_family_defines(self):
        if self.did.family not in STMHeader.CACHE_FAMILY:
            defines = []
            match = re.findall(r"if defined\((?P<define>STM32(?:F|G|L|H|W).....)\)", (self.cmsis_folder / self.family_header_file).read_text(encoding="utf-8", errors="replace"))
            if match: defines = match;
            else: LOGGER.error("Cannot find family defines for {}!".format(self.did.string));
            STMHeader.CACHE_FAMILY[self.did.family]["family_defines"] = defines
        return STMHeader.CACHE_FAMILY[self.did.family]["family_defines"]

    def _get_filtered_defines(self):
        defines = {}
        # get all the non-empty defines
        for define in self.header.defines:
            define = re.sub(r"/\*.*?\*/", "", define).strip()
            parts = define.split(" ")
            if len(parts) <= 1: continue;
            name = parts[0]
            if any(i in name for i in ["("]): continue;
            if any(name.endswith(i) for i in ["_IRQn", "_IRQHandler", "_SUPPORT", "_TypeDef"]): continue;
            if any(name.startswith(i) for i in ["IS_"]): continue;
            defines[name] = "".join(parts[1:]).strip()
        return defines

    def _get_defines(self):
        # create the destination directory
        destination = (STMHeader.CACHE_PATH / self.family_folder / self.header_file).with_suffix(".cpp").absolute()
        executable = destination.with_suffix("")
        defines = self._get_filtered_defines()
        if not executable.exists():
            # generate the cpp file from the template
            LOGGER.info("Generating {} ...".format(destination.name))
            substitutions = {"header": self.header_file, "defines": sorted(defines)}
            content = Environment().from_string(HEADER_TEMPLATE).render(substitutions)
            # write the cpp file into the cache
            destination.parent.mkdir(exist_ok=True, parents=True)
            destination.write_text(content)
            # compile file into an executable
            includes = [str(STMHeader.CMSIS_PATH.absolute()), str(self.cmsis_folder.absolute())]
            gcc_command = ["g++", "-Wno-narrowing",
                "-I{}".format(" -I".join(includes)),
                "-o {}".format(executable),
                str(destination)
            ]
            LOGGER.info("Compiling {} ...".format(destination.name))
            retval = subprocess.run(" ".join(gcc_command), shell=True)
            if retval.returncode:
                LOGGER.error("Header compilation failed! {}".format(retval));
                return None
        # execute the file
        LOGGER.info("Running {} ...".format(executable.name))
        retval = subprocess.run([str(executable)], stdout=subprocess.PIPE)
        if retval.returncode:
            LOGGER.error("Header execution failed! {}".format(retval));
            return None
        # parse the printed values
        localv = {}
        exec(retval.stdout, globals(), localv)
        undefined = [d for d in defines if d not in localv["cpp_defines"]]
        if len(undefined):
            LOGGER.warning("Undefined macros: {}".format(undefined))
        return localv["cpp_defines"]

    def _get_memmap(self):
        # get the values of the definitions in this file
        defines = self.get_defines();

        # get the mapping of peripheral to its type
        peripheral_map = {}
        seen_defines = []
        for name, value in self._get_filtered_defines().items():
            if "*)" in value:
                values = value.split("*)")
                typedef = values[0].strip()[2:].strip()
                peripheral_map[name] = (typedef, defines[name])
                LOGGER.debug("Found peripheral ({} *) {} @ 0x{:x}".format(typedef, name, defines[name]))

        # build the array containing the peripheral types
        raw_types = {typedef: [(v["type"], v["name"], int(v["array_size"], 16 if v["array_size"].startswith("0x") else 10) if v["array"] else 0)
                               for v in values["properties"]["public"]]
                     for typedef, values in self.header.classes.items()}

        # function to recursively flatten the types
        def _flatten_type(typedef, result, prefix=""):
            for (t, n, s) in raw_types[typedef]:
                if t in STMHeader.BUILTINS:
                    size = STMHeader.BUILTINS[t]
                    name = None if n.upper().startswith("RESERVED") else n
                    if s == 0:
                        result.append( (size, (prefix + name) if name else name) )
                    else:
                        if not name:
                            result.append( (size * s, name) )
                        else:
                            result.extend([(size, prefix + "{}.{}".format(name, ii)) for ii in range(s)])
                elif t in raw_types.keys():
                    if s == 0:
                        _flatten_type(t, result, prefix)
                    else:
                        for ii in range(s):
                            _flatten_type(t, result, prefix + "{}.{}.".format(n, ii))
                else:
                    LOGGER.error("Unknown type: {} ({} {})".format(t, n, s))
                    exit(1)

        # flatten all types
        flat_types = defaultdict(list)
        for typedef in raw_types:
            _flatten_type(typedef, flat_types[typedef])

        # match the macro definitions to the type structures
        matched_types = defaultdict(list)
        for typedef, pregs in flat_types.items():
            peri = "_".join([t for t in typedef.split("_") if t.isupper()])
            position = 0
            for reg in pregs:
                if reg[1] is None:
                    position += reg[0]
                    continue
                sreg = [r for r in reg[1].split(".") if r.isupper() or r.isdigit()]
                prefix = ["{}_{}_".format(peri, "".join([r for r in sreg if r.isupper()]))]
                if len(sreg) > 1:
                    if sreg[0].isdigit():
                        parts = sreg[1].split("R")
                        parts[-2] += sreg[0]
                        prefix.append("{}_{}_".format(peri, "R".join(parts)))
                    elif sreg[1].isdigit():
                        sreg[1] = str(int(sreg[1]) + 1)
                        prefix.append("{}_{}_".format(peri, "".join([r for r in sreg if r.isupper()]) + sreg[1]))
                        prefix.append("{}_{}x_".format(peri, "".join([r for r in sreg if r.isupper()])))
                if "FSMC_BTCR_" in prefix:
                    # This register is actually aliased
                    prefix.append("FSMC_BCRx_")
                    prefix.append("FSMC_BTRx_")

                regmap = {}
                for p in prefix:
                    keys = [d for d in defines.keys() if d.startswith(p)]
                    seen_defines.extend(keys)
                    regmap.update({k.replace(p, ""):defines[k] for k in keys})
                if not len(regmap):
                    LOGGER.debug("Empty: {:30} {}->{} ({} >> {})".format(typedef, peri, prefix, reg[1], sreg))
                    continue

                # convert macro names to positional arguments
                fields = sorted(list(set([r[:-4] for r in regmap if r.endswith("_Pos")])))
                registers = {}
                for field in fields:
                    regs = {k:v for k,v in regmap.items() if k == field or k.startswith(field + "_")}
                    val = regs.pop(field, None)
                    pos = regs.pop(field + "_Pos", None)
                    msk = regs.pop(field + "_Msk", None)
                    if val is None:
                        LOGGER.warning("{} not found: {}".format(field, regs))
                        continue
                    if pos is None:
                        LOGGER.warning("{}_Pos not found: {}".format(field, regs))
                        continue
                    if msk is None:
                        LOGGER.warning("{}_Msk not found: {}".format(field, regs))
                        continue

                    rem = {k.replace(field + "_", ""):v for k,v in regs.items()}
                    mask = msk >> pos
                    width = 0
                    while(mask):
                        width += 1
                        mask >>= 1
                    registers[pos] = (field, width, msk, val, rem)

                # print(registers)
                # Store in map
                matched_types[typedef].append( (position, reg[0], reg[1], registers) )
                position += reg[0]

        # print the remaining
        remaining_defines = [d for d in defines if d not in seen_defines and not d.endswith("_BASE")]
        for typedef in matched_types:
            peri = "_".join([t for t in typedef.split("_") if t.isupper()]) + "_"
            rem = [d for d in remaining_defines if d.startswith(peri)]
            if len(rem):
                LOGGER.warning("Unassigned defines for ({} *) {}: {}".format(typedef, peri, len(rem)))
                for d in rem:
                    LOGGER.debug("{}: {}".format(d, defines[d]))

        # for typedef, registers in matched_types.items():
        #     print(typedef)
        #     for reg in registers:
        #         print("    {:03x}: {}".format(reg[0], reg[2]))

        return (peripheral_map, matched_types)
