# -*- coding: utf-8 -*-
# Copyright (c) 2021, Christopher Durand
# All rights reserved.

import re
from pathlib import Path

ROOT_PATH = Path(__file__).parents[2]
CUBE_PATH = ROOT_PATH / "ext/stm32-cube-hal-drivers"
DMAMUX_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(LL_DMAMUX_REQ_\w+))\s+(?P<id>(0x[0-9A-Fa-f]+))U")
REQUEST_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(DMA_REQUEST_\w+))\s+(?P<id>([0-9]+))U")

def read_request_map(did):
    dma_header = _get_hal_dma_header_path(did.family)
    dmamux_header = _get_ll_dmamux_header_path(did.family)
    request_map = None
    if did.family in ["c0", "g4", "h7", "l5"]:
        request_map = _read_requests(dma_header)
    elif did.family in ["g0", "wb", "wl"]:
        request_map = _read_requests_from_ll_dmamux(dma_header, dmamux_header)
    elif did.family == "l4" and did.name[0] in ["p", "q", "r", "s"]:
        request_map = _read_requests_l4(did.name in ["p5", "q5"])
    else:
        raise RuntimeError("No DMAMUX request data available for {}".format(did))
    _fix_request_data(request_map)
    return request_map


def _fix_request_data(request_map):
    fix_requests = {}
    dac_pattern = re.compile(r"(?P<dac>(DAC[0-9]))_CHANNEL(?P<ch>[0-9])")
    for name, number in request_map.items():
        if name.startswith("GENERATOR"):
            fix_requests["DMA_" + name] = number
        elif name == "FMAC_READ":
            fix_requests["FMAC_RD"] = number
        elif name == "FMAC_WRITE":
            fix_requests["FMAC_WR"] = number
        elif name == "CORDIC_READ":
            fix_requests["CORDIC_RD"] = number
        elif name == "CORDIC_WRITE":
            fix_requests["CORDIC_WR"] = number
        elif name == "DCMI_PSSI":
            fix_requests["PSSI"] = number
        elif name == "TIM16_COM":
            fix_requests["TIM16_TRIG_COM"] = number
        elif name == "TIM17_COM":
            fix_requests["TIM17_TRIG_COM"] = number
        elif name == "HRTIM_MASTER":
            fix_requests["HRTIM1_M"] = number
        elif name.startswith("HRTIM_TIMER_"):
            fix_requests[name.replace("HRTIM_TIMER_", "HRTIM1_")] = number
        elif name == "SUBGHZSPI_RX":
            fix_requests["SUBGHZ_RX"] = number
        elif name == "SUBGHZSPI_TX":
            fix_requests["SUBGHZ_TX"] = number
        else:
            m = dac_pattern.match(name)
            if m:
                fix_requests["{}_CH{}".format(m.group("dac"), m.group("ch"))] = number

    request_map.update(fix_requests)

def _get_include_path(family):
    return CUBE_PATH / Path("stm32{}xx/Inc".format(family))


def _get_hal_dma_header_path(family):
    return _get_include_path(family) / Path("stm32{}xx_hal_dma.h".format(family))


def _get_ll_dmamux_header_path(family):
    return _get_include_path(family) / Path("stm32{}xx_ll_dmamux.h".format(family))


# For G4, H7 and L5
def _read_requests(hal_dma_file):
    requests_map = _read_map(hal_dma_file, REQUEST_PATTERN)
    out_map = {}
    for r in requests_map.keys():
        out_map[r.replace("DMA_REQUEST_", "", 1)] = int(requests_map[r])
    return out_map


# For G0, WB and WL
def _read_requests_from_ll_dmamux(hal_dma_file, ll_dmamux_file):
    dmamux_map = _read_map(ll_dmamux_file, DMAMUX_PATTERN)
    request_pattern = re.compile("^\s*#define\s+(?P<name>(DMA_REQUEST_\w+))\s+(?P<id>(LL_DMAMUX?_REQ_\w+))\s*")
    requests_map = _read_map(hal_dma_file, request_pattern)
    out_map = {}
    for r in requests_map.keys():
        out_map[r.replace("DMA_REQUEST_", "", 1)] = int(dmamux_map[requests_map[r]], 16)
    return out_map


# For L4+
def _read_requests_l4(read_for_p5_q5):
    out_map = {}
    p5_q5_if = "#if defined (STM32L4P5xx) || defined (STM32L4Q5xx)"
    if_pattern = re.compile(r"^\s*#\s*if\s+")
    else_pattern = re.compile(r"^\s*#\s*else")
    endif_pattern = re.compile(r"^\s*#\s*endif")
    in_p5_q5_section = False
    ignore = False
    with open(_get_hal_dma_header_path("l4"), "r") as header_file:
        if_counter = 0
        for line in header_file.readlines():
            if p5_q5_if in line:
                in_p5_q5_section = True
                ignore = not read_for_p5_q5
            elif in_p5_q5_section:
                if if_pattern.match(line):
                    if_counter += 1
                elif endif_pattern.match(line):
                    if if_counter == 0:
                        in_p5_q5_section = False
                        ignore = False
                    else:
                        if_counter -= 1
                elif else_pattern.match(line) and if_counter == 0:
                    ignore = read_for_p5_q5
            if not ignore:
                m = REQUEST_PATTERN.match(line)
                if m:
                    name = m.group("name").replace("DMA_REQUEST_", "", 1)
                    if name in out_map:
                        raise RuntimeError("Duplicate entry {}".format(name))
                    out_map[name] = int(m.group("id"))
    return out_map


def _read_map(filename, pattern):
    out_map = {}
    with open(filename, "r") as header_file:
        for line in header_file.readlines():
            m = pattern.match(line)
            if m:
                name = m.group("name")
                if name in out_map:
                    raise RuntimeError("Duplicate entry {}".format(name))
                out_map[name] = m.group("id")
    return out_map
