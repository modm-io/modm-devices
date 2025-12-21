# -*- coding: utf-8 -*-
# Copyright (c) 2021, Christopher Durand
# All rights reserved.

import re
from pathlib import Path

ROOT_PATH = Path(__file__).parents[2]
CUBE_PATH = ROOT_PATH / "ext/stm32-cube-hal-drivers"
DMAMUX_LL_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(LL_DMAMUX?_REQ_\w+))\s+(?P<id>(0x[0-9A-Fa-f]+))U")
REQUEST_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(DMA_REQUEST_\w+))\s+(?P<id>([0-9]+))U")
BDMA_REQUEST_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(BDMA_REQUEST_\w+))\s+(?P<id>([0-9]+))U")
DMAMUX_PATTERN = re.compile(r"^\s*#define\s+(?P<name>(DMAM?U?X?_REQU?E?S?T?_\w+))\s+(?P<id>(LL_DMAMUX?_REQ_\w+))\s*")

def read_request_map(did):
    dma_header = _get_hal_dma_header_path(did)
    dmamux_header = _get_ll_dmamux_header_path(did)
    request_map = None
    if did.family in ["c0", "g4", "h7", "l5"]:
        request_map = _read_requests(dma_header, REQUEST_PATTERN)
    elif did.family in ["g0", "u0", "wb", "wl"]:
        request_map = _read_requests_from_ll_dmamux(dma_header, dmamux_header)
    elif did.family == "l4" and did.name[0] in ["p", "q", "r", "s"]:
        request_map = _read_requests_l4(dma_header, dmamux_header, did)
    else:
        raise RuntimeError("No DMAMUX request data available for {}".format(did))
    _fix_request_data(request_map, "DMA")
    return request_map


def read_bdma_request_map(did):
    dma_header = _get_hal_dma_header_path(did)
    request_map = _read_requests(dma_header, BDMA_REQUEST_PATTERN)
    _fix_request_data(request_map, "BDMA")
    return request_map


def _fix_request_data(request_map, prefix):
    fix_requests = {}
    dac_pattern = re.compile(r"(?P<dac>(DAC[0-9]))_CHANNEL(?P<ch>[0-9])")
    for name, number in request_map.items():
        if name.startswith("GENERATOR"):
            fix_requests[prefix + "_" + name] = number
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
        elif name == "DAC":
            fix_requests["DAC_OUT1"] = number
        elif name == "USART_TX":
            fix_requests["USART1_TX"] = number
        elif name == "USART_RX":
            fix_requests["USART1_RX"] = number
        elif name == "LPUART_TX":
            fix_requests["LPUART1_TX"] = number
        elif name == "LPUART_RX":
            fix_requests["LPUART1_RX"] = number
        else:
            m = dac_pattern.match(name)
            if m:
                fix_requests["{}_CH{}".format(m.group("dac"), m.group("ch"))] = number

    request_map.update(fix_requests)

def _get_family(did):
    family = f"{did.family}xx"
    if did.string[5:8] in ["h7r", "h7s"]:
        family = "h7rsxx"
    elif did.string[5:8] == "wb0":
        family = "wb0x"
    elif did.string[5:8] == "wba":
        family = "wbax"
    elif did.string[5:8] == "wl3":
        family = "wl3x"
    return family


def _get_include_path(family):
    return CUBE_PATH / Path("stm32{}/Inc".format(family))


def _get_hal_dma_header_path(did):
    family = _get_family(did)
    return _get_include_path(family) / Path("stm32{}_hal_dma.h".format(family))


def _get_ll_dmamux_header_path(did):
    family = _get_family(did)
    return _get_include_path(family) / Path("stm32{}_ll_dmamux.h".format(family))


# For G4, H7 and L5
def _read_requests(hal_dma_file, request_pattern):
    requests_map = _read_map(hal_dma_file, request_pattern)
    out_map = {}
    for r in requests_map.keys():
        prefix = "BDMA" if "BDMA" in r else "DMA"
        out_map[r.replace(prefix + "_REQUEST_", "", 1)] = int(requests_map[r])
    return out_map


# For G0, WB and WL
def _read_requests_from_ll_dmamux(hal_dma_file, ll_dmamux_file):
    dmamux_map = _read_map(ll_dmamux_file, DMAMUX_LL_PATTERN)
    requests_map = _read_map(hal_dma_file, DMAMUX_PATTERN)
    out_map = {}
    for r in requests_map.keys():
        out_map[r.replace("DMA_REQUEST_", "", 1).replace("DMAMUX_REQ_", "", 1)] = int(dmamux_map[requests_map[r]], 16)
    return out_map


# For L4+
def _read_requests_l4(hal_dma_file, ll_dmamux_file, did):
    dmamux_pattern = re.compile(r"^\s*#define\s+(?P<name>(LL_DMAMUX_REQ_\w+))\s+(?P<id>\(? ?\d+)U")
    dmamux_map = _read_map(ll_dmamux_file, dmamux_pattern, ignore_duplicates=True)
    del dmamux_map["LL_DMAMUX_REQ_ADC2_SHIFT"]
    if (is_p5_q5 := did.name in ["p5", "q5"]):
        dmamux_map = {k: ((int(v[1:]) + 1) if "(" in v else v) for k, v in dmamux_map.items()}
    else:
        dmamux_map = {k: v.replace("(", "") for k, v in dmamux_map.items() if k != "LL_DMAMUX_REQ_ADC2"}

    requests_map = _read_map(hal_dma_file, DMAMUX_PATTERN)
    if not is_p5_q5:
        del requests_map["DMA_REQUEST_ADC2"]

    out_map = {}
    for r in requests_map.keys():
        out_map[r.replace("DMA_REQUEST_", "", 1).replace("DMAMUX_REQ_", "", 1)] = int(dmamux_map[requests_map[r]])
    return out_map


def _read_map(filename, pattern, ignore_duplicates=False):
    out_map = {}
    with open(filename, "r") as header_file:
        for line in header_file.readlines():
            m = pattern.match(line)
            if m:
                name = m.group("name")
                if name in out_map and not ignore_duplicates:
                    raise RuntimeError("Duplicate entry {}".format(name))
                out_map[name] = m.group("id")
    return out_map
