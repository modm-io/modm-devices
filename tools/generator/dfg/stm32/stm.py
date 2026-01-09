# -*- coding: utf-8 -*-
# Copyright (c) 2015-2016, Niklas Hauser
# All rights reserved.

import re
import logging

LOGGER = logging.getLogger("dfg.stm.data")

ignored_devices = \
[
    "STM32WL5M",
    "STM32WB1M",
    "STM32WB5M",
]

def ignoreDevice(device_id: str) -> bool:
    for ignore in ignored_devices:
        if device_id.startswith(ignore):
            return True
    return False

# ================================ CMSIS DEFINE ===============================
def getDefineForDevice(device_id, familyDefines):
    if len(familyDefines) == 1:
        return familyDefines[0]

    # get all defines for this device name
    devName = 'STM32{}{}'.format(device_id.family.upper(), device_id.name.upper())

    # Map STM32WL33 -> STM32WL3X
    if device_id.family == 'wl' and devName[7:9] in ["30", "31", "33"]:
        devName = devName[:-1] + 'X'

    deviceDefines = sorted([define for define in familyDefines if define.startswith(devName)])
    # if there is only one define thats the one
    if len(deviceDefines) == 1:
        return deviceDefines[0]

    # now we match for the size-id.
    devNameMatch = devName + 'x{}'.format(device_id.size.upper())
    for define in deviceDefines:
        if devNameMatch <= define:
            return define

    # now we match for the pin-id.
    devNameMatch = devName + '{}x'.format(device_id.pin.upper())
    for define in deviceDefines:
        if devNameMatch <= define:
            return define

    return None

# ================================ GPIO REMAP =================================
stm32f1_gpio_remap = \
{
    # (position % 32) -> local bit position
    # MAPR register
    'spi1':         {'position':  0, 'mask': 1, 'mapping': [0, 1]},
    'i2c1':         {'position':  1, 'mask': 1, 'mapping': [0, 1]},
    'usart1':       {'position':  2, 'mask': 1, 'mapping': [0, 1]},
    'usart2':       {'position':  3, 'mask': 1, 'mapping': [0, 1]},
    'usart3':       {'position':  4, 'mask': 3, 'mapping': [0, 1,    3]},
    'tim1':         {'position':  6, 'mask': 3, 'mapping': [0, 1,    3]},
    'tim2':         {'position':  8, 'mask': 3, 'mapping': [0, 1, 2, 3]},
    'tim3':         {'position': 10, 'mask': 3, 'mapping': [0, 0, 2, 3]}, # CubeMX db bug
    'tim4':         {'position': 12, 'mask': 1, 'mapping': [0, 1]},
    'can':          {'position': 13, 'mask': 3, 'mapping': [0,    2, 3]},
    'can1':         {'position': 13, 'mask': 3, 'mapping': [0,    2, 3]},
    'pd01':         {'position': 15, 'mask': 1, 'mapping': [0, 1]},
    'tim5ch4':      {'position': 16, 'mask': 1, 'mapping': [0, 1]},
    'adc1etrginj':  {'position': 17, 'mask': 1, 'mapping': [0, 1]},
    'adc1etrgreg':  {'position': 18, 'mask': 1, 'mapping': [0, 1]},
    'adc2etrginj':  {'position': 19, 'mask': 1, 'mapping': [0, 1]},
    'adc2etrgreg':  {'position': 20, 'mask': 1, 'mapping': [0, 1]},
    'eth':          {'position': 21, 'mask': 1, 'mapping': [0, 1]},
    'can2':         {'position': 22, 'mask': 1, 'mapping': [0, 1]},
    'mii_rmii_sel': {'position': 23, 'mask': 1, 'mapping': [0, 1]},
    'swj_cfg':      {'position': 24, 'mask': 7, 'mapping': [0, 1, 2,    4]},
    # position 27 is empty
    'spi3':         {'position': 28, 'mask': 1, 'mapping': [0, 1]},
    'i2s3':         {'position': 28, 'mask': 1, 'mapping': [0, 1]},
    'tim2itr1':     {'position': 29, 'mask': 1, 'mapping': [0, 1]},
    'ptp_pps':      {'position': 30, 'mask': 1, 'mapping': [0, 1]},
    # position 31 is empty
    # MAPR2 register
    'tim15':        {'position': 32, 'mask': 1, 'mapping': [0, 1]},
    'tim16':        {'position': 33, 'mask': 1, 'mapping': [0, 1]},
    'tim17':        {'position': 34, 'mask': 1, 'mapping': [0, 1]},
    'cec':          {'position': 35, 'mask': 1, 'mapping': [0, 1]},
    'tim1_dma':     {'position': 36, 'mask': 1, 'mapping': [0, 1]},
    'tim9':         {'position': 37, 'mask': 1, 'mapping': [0, 1]},
    'tim10':        {'position': 38, 'mask': 1, 'mapping': [0, 1]},
    'tim11':        {'position': 39, 'mask': 1, 'mapping': [0, 1]},
    'tim13':        {'position': 40, 'mask': 1, 'mapping': [0, 1]},
    'tim14':        {'position': 41, 'mask': 1, 'mapping': [0, 1]},
    'fsmc_nadv':    {'position': 42, 'mask': 1, 'mapping': [0, 1]},
    'tim67_dac_dma':{'position': 43, 'mask': 1, 'mapping': [0, 1]},
    'tim12':        {'position': 44, 'mask': 1, 'mapping': [0, 1]},
    'misc':         {'position': 45, 'mask': 1, 'mapping': [0, 1]},
}

def getGpioRemapForModuleConfig(module, config):
    mmm = {}
    if module in stm32f1_gpio_remap:
        mmm['mask'] = stm32f1_gpio_remap[module]['mask']
        mmm['position'] = stm32f1_gpio_remap[module]['position']
        mmm['mapping'] = stm32f1_gpio_remap[module]['mapping'][int(config)]
    return mmm

# =============================== FLASH LATENCY ===============================
stm32_flash_latency = \
{
    'f0': {
        1800: [24, 48]
    },
    'f1': [
        {'name': ['00'], 1800: [24]},
        {1800: [24, 48, 72]}
    ],
    'f2': {
        2700: [30, 60, 90, 120],
        2400: [24, 48, 72, 96, 120],
        2100: [18, 36, 54, 72, 90, 108, 120],
        1800: [16, 32, 48, 64, 80, 96, 112, 120]
    },
    'f3': {
        1800: [24, 48, 72]
    },
    'f4': [{
      'name': ['10', '11', '12', '13', '23'],
        2700: [30, 60, 90, 100],
        2400: [24, 48, 72, 96, 100],
        2100: [18, 36, 54, 72, 90, 100],
        1800: [16, 32, 48, 64, 80, 96, 100]
    },{
      'name': ['01'],
        2700: [30, 60, 84],
        2400: [24, 48, 72, 84],
        2100: [18, 36, 54, 72, 84],
        1800: [16, 32, 48, 64, 80, 84]
    },{
      'name': ['05', '07', '15', '17'],
        2700: [30, 60, 90, 120, 150, 168],
        2400: [24, 48, 72, 96, 120, 144, 168],
        2100: [22, 44, 66, 88, 110, 132, 154, 168],
        1800: [20, 40, 60, 80, 100, 120, 140, 160]
    },{
      'name': ['27', '29', '37', '39', '46', '69', '79'],
        2700: [30, 60, 90, 120, 150, 180],
        2400: [24, 48, 72, 96, 120, 144, 168, 180],
        2100: [22, 44, 66, 88, 110, 132, 154, 176, 180],
        1800: [20, 40, 60, 80, 100, 120, 140, 160, 168]
    }],
    'f7': {
        2700: [30, 60, 90, 120, 150, 180, 216],
        2400: [24, 48, 72, 96, 120, 144, 168, 192, 216],
        2100: [22, 44, 66, 88, 110, 132, 154, 176, 198, 216],
        1800: [20, 40, 60, 80, 100, 120, 140, 160, 180]
    },
    'l0': {
        1650: [16, 32],
        1350: [8, 16],
        1050: [4.2]
    },
    'l1': [{ # Cat 1
      'size': ['6', '8', 'b'],
        1800: [16, 32],
        1500: [8, 16],
        1200: [4.2, 8]
    },{ # Cat 2,3,4,5,6
        1800: [16, 32],
        1500: [8, 16],
        1200: [2.1, 4.2]
    }],
    'l4': [{ # L4+ devices
      'name': ['r5', 'r7', 'r9', 's5', 's7', 's9', 'p5', 'q5'],
        1200: [20, 40, 60, 80, 120],
        1000: [8, 16, 26]
    },{ # L4 devices
        1200: [16, 32, 48, 64, 80],
        1000: [6, 12, 18, 26]
    }],
    'l5': {
        1280: [20, 40, 60, 80, 110],  # Vcore range 0
        1200: [20, 40, 60, 80],       # Vcore range 1
        1000: [8, 16, 26],            # Vcore range 2
    },
    'c0': {
        1200: [24, 48],
    },
    'g0': {
        1200: [24, 48, 64],
        1000: [8, 16]
    },
    'g4': {
        1280: [20, 40, 60, 80, 100, 120, 140, 160, 170],
        1000: [8, 16, 26]
    },
    'h5': {
        1260: [42, 84, 126, 168, 210, 250],
        1150: [34, 68, 102, 136, 170, 200],
        1050: [30, 60, 90, 120, 150],
        950: [20, 40, 60, 80, 100]
    },
    'h7': [{
      'name': ['23', '25', '30', '33', '35'],
        1260: [70, 140, 210, 275],
        1150: [67, 133, 200],
        1050: [50, 100, 150],
        950: [35, 70, 85],
    },{
      'name': ['a0', 'a3', 'b0', 'b3'],
        1250: [42, 84, 126, 168, 210, 252, 280],
        1150: [38, 76, 114, 152, 190, 225],
        1050: [34, 68, 102, 136, 160],
        950: [22, 44, 66, 88],
    },{ # The remaining devices
        1260: [70, 140, 210, 225, 240],
        1150: [70, 140, 210, 225],
        1050: [55, 110, 165, 225],
        950: [45, 90, 135, 180, 225],
    }],
    'wb': {
        1200: [18, 36, 54, 64],
        1000: [6, 12, 16]
    },
    'wl': {
        1200: [18, 36, 48],
        1000: [6, 12, 16]
    },
    'u0': {
        1200: [24, 48, 56],
        1000: [8, 16, 16]
    },
    'u3': {
        900: [32, 64, 96],
        750: [16, 32, 48]
    },
    'u5': {
        1200: [32, 64, 96, 128, 160],
        1100: [30, 60, 90, 110],
        1000: [24, 48, 55],
        900: [12, 25],
    },
}

def getFlashLatencyForDevice(did):
    lts = stm32_flash_latency.get(did.family)
    if lts is None: return {}; # family not known
    # Convert MHz to Hz and filter out string keys
    lconv = lambda l: {k:[int(f*1e6) for f in v] for k, v in l.items() if isinstance(k, int)}
    if isinstance(lts, dict): return lconv(lts); # whole family uses same table
    for lt in lts:
        # check if all conditions match
        if all(did[k] in v for k, v in lt.items() if isinstance(k, str)):
            return lconv(lt) # return filtered table
    return lconv(lts[-1]) # if non were found, return last table


# ==================================== DMA ====================================
stm32f3_dma_remap = \
{
    'dma1ch1': {
        'tim17_ch1':  'tim17_up',
        'tim17_up':  {'position': 12, 'mask': 1, 'id': 0},
    },
    'dma1ch2': {
        'adc2':      {'position': 72, 'mask': 3, 'id': 2},
        'i2c_tx':    {'position': 70, 'mask': 3, 'id': 1},
        'spi_rx':    {'position': 64, 'mask': 3, 'id': 0}, # also 'id': 3
    },
    'dma1ch3': {
        'dac1_ch1':   'tim6_up',
        'i2c_rx':    {'position': 68, 'mask': 3, 'id': 1},
        'spi_tx':    {'position': 66, 'mask': 3, 'id': 0}, # also 'id': 3
        'tim16_ch1':  'tim16_up',
        'tim16_up':  {'position': 11, 'mask': 1, 'id': 0},
        'tim6_up':   {'position': 13, 'mask': 1, 'id': 1},
    },
    'dma1ch4': {
        'adc2':      {'position': 72, 'mask': 3, 'id': 3},
        'dac1_ch2':   'tim7_up',
        'i2c_tx':    {'position': 70, 'mask': 3, 'id': 2},
        'spi_rx':    {'position': 64, 'mask': 3, 'id': 1},
        'tim7_up':   {'position': 14, 'mask': 1, 'id': 1},
    },
    'dma1ch5': {
        'dac2_ch1':   'tim18_up',
        'i2c_rx':    {'position': 68, 'mask': 3, 'id': 2},
        'spi_tx':    {'position': 66, 'mask': 3, 'id': 1},
        'tim18_up':  {'position': 15, 'mask': 1, 'id': 1},
    },
    'dma1ch6': {
        'i2c_tx':    {'position': 70, 'mask': 3, 'id': 0}, # also 'id': 3
        'spi_rx':    {'position': 64, 'mask': 3, 'id': 2},
    },
    'dma1ch7': {
        'i2c_rx':    {'position': 68, 'mask': 3, 'id': 0}, # also 'id': 3
        'spi_tx':    {'position': 66, 'mask': 3, 'id': 2},
        'tim17_ch1':  'tim17_up',
        'tim17_up':  {'position': 12, 'mask': 1, 'id': 1},
    },


    'dma2ch1': {
        'adc2':     [{'position':  8, 'mask': 1, 'id': 0},
                     {'position': 73, 'mask': 1, 'id': 0}],
        'adc4':      {'position':  8, 'mask': 1, 'id': 0},
    },
    'dma2ch3': {
        'adc2':     [{'position':  8, 'mask': 1, 'id': 1},
                     {'position': 73, 'mask': 1, 'id': 0}],
        'adc4':      {'position':  8, 'mask': 1, 'id': 1},
        'dac1_ch1':   'tim6_up',
        'tim6_up':   {'position': 13, 'mask': 1, 'id': 0},
    },
    'dma2ch4': {
        'dac1_ch2':   'tim7_up',
        'tim7_up':   {'position': 14, 'mask': 1, 'id': 0},
    },
    'dma2ch5': {
        'dac2_ch1':   'tim18_up',
        'tim18_up':  {'position': 15, 'mask': 1, 'id': 0},
    },
}

stm32f0_dma_remap = \
{
    'dma1ch1': {
        'tim17_up': [{'position': 14, 'mask': 1, 'id': 1},
                     {'position': 12, 'mask': 1, 'id': 0}],
        'tim17_ch1':  'tim17_up',
        'adc':       {'position':  8, 'mask': 1, 'id': 0},
    },
    'dma1ch2': {
        'tim1_ch1':  {'position': 28, 'mask': 1, 'id': 0},
        'i2c1_tx':   {'position': 27, 'mask': 1, 'id': 0},
        'usart3_tx': {'position': 26, 'mask': 1, 'id': 1},
        'tim17_up': [{'position': 14, 'mask': 1, 'id': 1},
                     {'position': 12, 'mask': 1, 'id': 1}],
        'tim17_ch1':  'tim17_up',
        'usart1_tx': {'position':  9, 'mask': 1, 'id': 0},
        'adc':       {'position':  8, 'mask': 1, 'id': 1},
    },
    'dma1ch3': {
        'tim1_ch2':  {'position': 28, 'mask': 1, 'id': 0},
        'tim2_ch2':  {'position': 29, 'mask': 1, 'id': 0},
        'i2c1_rx':   {'position': 27, 'mask': 1, 'id': 0},
        'usart3_rx': {'position': 26, 'mask': 1, 'id': 1},
        'tim16_up': [{'position': 13, 'mask': 1, 'id': 1},
                     {'position': 11, 'mask': 1, 'id': 0}],
        'tim16_ch1':  'tim16_up',
        'usart1_rx': {'position': 10, 'mask': 1, 'id': 0},
    },
    'dma1ch4': {
        'tim1_ch3':  {'position': 28, 'mask': 1, 'id': 0},
        'tim3_trig': {'position': 30, 'mask': 1, 'id': 0},
        'tim3_ch1':   'tim3_trig',
        'tim2_ch4':  {'position': 29, 'mask': 1, 'id': 0},
        'usart2_tx': {'position': 25, 'mask': 1, 'id': 0},
        'spi2_rx':   {'position': 24, 'mask': 1, 'id': 0},
        'tim16_up': [{'position': 13, 'mask': 1, 'id': 1},
                     {'position': 11, 'mask': 1, 'id': 1}],
        'tim16_ch1':  'tim16_up',
        'usart1_tx': {'position':  9, 'mask': 1, 'id': 1},
    },
    'dma1ch5': {
        'usart2_rx': {'position': 25, 'mask': 1, 'id': 0},
        'spi2_tx':   {'position': 24, 'mask': 1, 'id': 0},
        'usart1_rx': {'position': 10, 'mask': 1, 'id': 1},
    },
    'dma1ch6': {
        'tim3_trig': {'position': 30, 'mask': 1, 'id': 1},
        'tim3_ch1':   'tim3_trig',
        'tim1_ch1':  {'position': 28, 'mask': 1, 'id': 1},
        'tim1_ch2':   'tim1_ch1',
        'tim1_ch3':   'tim1_ch1',
        'i2c1_tx':   {'position': 27, 'mask': 1, 'id': 1},
        'usart3_rx': {'position': 26, 'mask': 1, 'id': 0},
        'usart2_rx': {'position': 25, 'mask': 1, 'id': 1},
        'spi2_rx':   {'position': 24, 'mask': 1, 'id': 1},
        'tim16_up':  {'position': 13, 'mask': 1, 'id': 1},
        'tim16_ch1':  'tim16_up',
    },
    'dma1ch7': {
        'tim2_ch2':  {'position': 29, 'mask': 1, 'id': 1},
        'tim2_ch4':   'tim2_ch2',
        'i2c1_rx':   {'position': 27, 'mask': 1, 'id': 1},
        'usart3_tx': {'position': 26, 'mask': 1, 'id': 0},
        'usart2_tx': {'position': 25, 'mask': 1, 'id': 1},
        'spi2_tx':   {'position': 24, 'mask': 1, 'id': 1},
        'tim17_up':  {'position': 14, 'mask': 1, 'id': 1},
        'tim17_ch1':  'tim17_up',
    },
}

def getDmaRemap(did, dma, channel, driver, inst, signal):
    if did.family == "f0":
        remap = stm32f0_dma_remap
    elif did.family == "f3":
        remap = stm32f3_dma_remap
    else:
        return None

    key1 = "dma{}ch{}".format(dma, channel)
    key2 = (driver + inst if inst else "") + ("_{}".format(signal) if signal else "")

    signals = remap.get(key1, {})
    signal = signals.get(key2, None)
    if signal is None:
        return None

    if isinstance(signal, str):
        signal = signals.get(signal)

    if isinstance(signal, dict):
        signal = [signal]

    # print(key1, key2, signal)
    assert( isinstance(signal, list) )
    return signal

# =================================== MEMORY ==================================
def add_ram(m, name, size, start=None, target=None, access=None):
    if name in m: return
    if target: m[target]["size"] -= size
    m[name] = {
        "access": "rwx" if access is None else access,
        "start": m[target]["start"] + m[target]["size"] if start is None else start,
        "size": size
    }


def stm32_memory_rename(name, data):
    renames = {
        "irom1": "flash",
        "main_flash": "flash",
        "flash-secure": "flash_s",
        "flash-non-secure": "flash_ns",
        "flash_bank1": "flash1",
        "flash_bank2": "flash2",

        "iram1": "sram1",
        "iram2": "sram2",
        "sram-secure": "sram_s",
        "sram-non-secure": "sram_ns",
        "sram1_2": "sram1",
        "ram_d1": "d1_sram",
        "ram_d2": "d2_sram1",
        "ram_d2s2": "d2_sram2",
        "ram_d2s3": "d2_sram3",
        "ram_d3": "d3_sram",
        "axi_sram": "d1_sram",
        "ahb_sram": "d2_sram1",

        "ccm_ram": "ccm",
        "dtcmram": "dtcm",
        "dtcm_ram": "dtcm",

        "bkp_sram": "backup",
    }
    name = renames.get(name, name)
    # also fix any potential aliases
    data["alias"] = renames.get(data["alias"], data["alias"])

    # EEPROM is not explicitly listed in STM32 memory map, but we can deduce it
    if "_eeprom.flm" in name: name = "eeprom"

    return name


def fixMemoryForDevice(did, memories: dict[str, dict], header) -> list[dict]:
    mems = {}
    for name, data in memories.items():
        name = stm32_memory_rename(name, data)
        if ".flm" in name: continue
        # remove empty aliases
        if not data["alias"]: del data["alias"]

        # Fix access for FLASH and EEPROM
        if "flash" in name: data["access"] = "rx"
        if "eeprom" in name: data["access"] = "r"
        # On STM32F4 CCM memory is rw only
        if did.family in ["f4", "l4"] and data["start"] == 0x10000000:
            name = "ccm"
            data["access"] = "rw"

        mems[name] = data

    # Correct memories for specific devices
    if did.family == "f2":
        # Split SRAM1 into SRAM1/2
        mems["sram1"] = mems.pop("sram")
        add_ram(mems, "sram2", 16*1024, target="sram1")

    elif did.family == "f3" and did.name in ["03", "28", "58", "98"]:
        ccm = 4 # Add CCM memory manually, since the headers are not helpful
        if did.size in ["b", "c"]: ccm = 8
        elif did.size in ["d", "e"]: ccm = 16
        add_ram(mems, "ccm", ccm*1024, start=0x10000000, target="sram")
        # F3x8 devices do not count the CCM memory as part of SRAM1
        if did.name == "58": mems["sram"]["size"] = 40*1024
        if did.name == "98": mems["sram"]["size"] = 64*1024

    elif did.family == "f4":
        # add CCM and Backup SRAM memories manually, since the headers are not helpful
        if did.name not in ["01", "10", "11", "12", "46"]:
            mems["backup"] = {"start": 0x40024000, "size": 4096, "access": "rwx"}
            mems["ccm"] = {"start": 0x10000000, "size": 64*1024, "access": "rw"}
        # Split SRAM1 into SRAM1/2/3
        sram2, sram3 = 0, 0
        if did.name in ["05", "07", "15", "17"]: sram2 = 16
        elif did.name in ["27", "29", "37", "39"]: sram2, sram3 = 16, 64
        elif did.name in ["69", "79"]: sram2, sram3 = 32, 128

        if (sram2 or sram3) and "sram" in mems:
            mems["sram1"] = mems.pop("sram")
        if sram3: add_ram(mems, "sram3", sram3*1024, target="sram1")
        if sram2: add_ram(mems, "sram2", sram2*1024, target="sram1")

    elif did.family == "f7":
        # Fix missing alias, ITCM_FLASH is faster
        mems["flash"]["alias"] = "itcm_flash"

    elif did.family == "g4":
        # Fix missing CCM and SRAM2
        sizes = header.get_memory_sizes()
        add_ram(mems, "ccm", sizes["CCMSRAM"], start=0x10000000, target="sram")
        if (sram2 := sizes.get("SRAM2")):
            mems["sram1"] = mems.pop("sram")
            add_ram(mems, "sram2", sram2, target="sram1")

    elif did.family == "h5":
        # Fix missing Backup and SRAM2/3
        sizes = header.get_memory_sizes()
        if (sram3 := sizes.get("SRAM3")): add_ram(mems, "sram3", sram3, target="sram1")
        if (sram2 := sizes.get("SRAM2")): add_ram(mems, "sram2", sram2, target="sram1")
        mems["backup"] = {"start": 0x40036400, "size": sizes["BKPSRAM"], "access": "rwx"}

    elif did.family == "h7":
        # Fix missing ITCM and Backup memory
        mems["backup"] = {"start": 0x38800000, "size": 4096, "access": "rwx"}
        if "m7" in did.get("core", "m7"):
            mems["itcm"] = {"start": 0, "size": 64*1024, "access": "rwx"}

        d2_sram2, d2_sram3 = 0, 0
        if did.name[0] in "23":
            d2_sram2 = 16
        if did.name[0] in "45" and did.name[1] in "357" and did.get("core", "m4") == "m4":
            d2_sram2, d2_sram3 = 128, 32
            # CM4 also missing d3_SRAM
            mems["d3_sram"] = {"start": 0x38000000, "size": 64*1024, "access": "rwx"}

        if d2_sram3: add_ram(mems, "d2_sram3", d2_sram3*1024, target="d2_sram1")
        if d2_sram2: add_ram(mems, "d2_sram2", d2_sram2*1024, target="d2_sram1")

        for name, data in mems.items():
            if "flash" not in name: data["access"] = "rwx"

    elif did.family == "u5":
        # Fix missing Backup memory
        mems["backup"] = {"start": 0x40036400, "size": 2048, "access": "rwx"}

    return [{"name": name} | data for name, data in mems.items()]

