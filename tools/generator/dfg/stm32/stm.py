# -*- coding: utf-8 -*-
# Copyright (c) 2015-2016, Niklas Hauser
# All rights reserved.

import logging

LOGGER = logging.getLogger("dfg.stm.data")

def getDefineForDevice(device_id, familyDefines):
    # get all defines for this device name
    devName = 'STM32{}{}'.format(device_id.family.upper(), device_id.name.upper())

    # Map STM32F7x8 -> STM32F7x7
    if device_id.family == 'f7' and devName[8] == '8':
        devName = devName[:8] + '7'

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
    'tim3':         {'position': 10, 'mask': 3, 'mapping': [0,    2, 3]},
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
    'g0': {
        1200: [24, 48, 64],
        1000: [8, 16]
    },
    'g4': {
        1280: [20, 40, 60, 80, 100, 120, 140, 160, 170],
        1000: [8, 16, 26]
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


stm32_memory = \
{
    'f0': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['30', '31', '38', '42', '48', '51', '58', '70', '71', '72', '78', '91', '98'],
                'memories': {'flash': 0, 'sram1': 0}
            }
        ]
    },
    'g0': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['30', '31', '41', '50', '51', '61', '70', '71', '81', 'b0', 'b1', 'c0', 'c1'],
                'memories': {'flash': 0, 'sram1': 0}
            }
        ]
    },
    'g4': {
        'start': {
            'flash': 0x08000000,
            'ccm': 0x10000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['31', '41'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2':  6*1024, 'ccm': 10*1024}
            },
            {
                'name': ['71', '91', 'a1'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 16*1024, 'ccm': 16*1024}
            },
            {
                'name': ['73', '74', '83', '84'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 16*1024, 'ccm': 32*1024}
            }
        ]
    },
    'f1': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['00', '01', '02', '03', '05', '07'],
                'memories': {'flash': 0, 'sram1': 0}
            }
        ]
    },
    'f2': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['05', '07', '15', '17'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 16*1024}
            }
        ]
    },
    'f3': {
        'start': {
            'flash': 0x08000000,
            'ccm': 0x10000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name' : ['01', '02', '18', '78', '73'],
                'memories' : {'flash': 0, 'sram1' : 0}
            },
            {
                'name': ['03', '28', '34'],
                'size': ['4', '6', '8'],
                'memories': {'flash': 0, 'ccm': 4*1024, 'sram1': 0}
            },
            {
                'name': ['03', '58'],
                'size': ['b', 'c'],
                'memories': {'flash': 0, 'ccm': 8*1024, 'sram1': 0}
            },
            {
                'name': ['03', '98'],
                'size': ['d', 'e'],
                'memories': {'flash': 0, 'ccm': 16*1024, 'sram1': 0}
            }
        ]
    },
    'f4': {
        'start': {
            'flash': 0x08000000,
            'ccm': 0x10000000,
            'sram': 0x20000000,
            'backup': 0x40024000
        },
        'model': [
            {
                'name' : ['01', '10', '11', '12', '46'],
                'memories' : {'flash': 0, 'sram1' : 0}
            },
            {
                'name': ['05', '07', '15', '17'],
                'memories': {'flash': 0, 'ccm': 64*1024, 'sram1': 0, 'sram2': 16*1024, 'backup': 4*1024}
            },
            {
                'name': ['13', '23'],
                'memories': {'flash': 0, 'ccm': 64*1024, 'sram1': 0, 'backup': 4*1024}
            },
            {
                'name': ['27', '29', '37', '39'],
                'memories': {'flash': 0, 'ccm': 64*1024, 'sram1': 0, 'sram2': 16*1024, 'sram3': 64*1024, 'backup': 4*1024}
            },
            {
                'name': ['69', '79'],
                'memories': {'flash': 0, 'ccm': 64*1024, 'sram1': 0, 'sram2': 32*1024, 'sram3': 128*1024, 'backup': 4*1024}
            }
        ]
    },
    'f7': {
        'start': {
            'flash': 0x00200000,
            'dtcm': 0x20000000,
            'itcm': 0x00000000,
            'sram': 0x20010000,
            'backup': 0x40024000
        },
        'model': [
            {
                'name': ['22', '32', '23', '30', '33', '45', '46', '50', '56'],
                'memories': {'flash': 0, 'itcm': 16*1024, 'dtcm': 64*1024, 'sram1': 0, 'sram2': 16*1024, 'backup': 4*1024}
            },
            {
                'name': ['65', '67', '68', '69', '77', '78', '79'],
                'memories': {'flash': 0, 'itcm': 16*1024, 'dtcm': 128*1024, 'sram1': 0, 'sram2': 16*1024, 'backup': 4*1024},
                'start': {'sram': 0x20020000} # overwrite due to bigger dtcm size!
            }
        ]
    },
    'h7': {
        'start': {
            'flash': 0x08000000,
            'dtcm': 0x20000000,
            'itcm': 0x00000000,
            'd1_sram': 0x24000000,
            'd2_sram': 0x30000000,
            'd3_sram': 0x38000000,
            'backup': 0x38800000
        },
        'model': [
            {
                'name': ['42'],
                'memories': {'flash': 0, 'itcm': 64*1024, 'dtcm': 128*1024, 'backup': 4*1024,
                             'd1_sram': 384*1024,
                             'd2_sram1': 32*1024, 'd2_sram2': 16*1024,
                             'd3_sram': 64*1024}
            },
            {
                'name': ['23', '25', '30', '33', '35'],
                'memories': {'flash': 0, 'itcm': 64*1024, 'dtcm': 128*1024, 'backup': 4*1024,
                             'd1_sram': 320*1024,
                             'd2_sram1': 16*1024, 'd2_sram2': 16*1024,
                             'd3_sram': 16*1024}
            },
            {
                'name': ['40', '43', '50', '53'],
                'memories': {'flash': 0, 'itcm': 64*1024, 'dtcm': 128*1024, 'backup': 4*1024,
                             'd1_sram': 512*1024,
                             'd2_sram1': 128*1024, 'd2_sram2': 128*1024, 'd2_sram3': 32*1024,
                             'd3_sram': 64*1024}
            },
            {
                'name': ['45', '47', '55', '57'],
                'core': ['m7'],
                'memories': {'flash': 0, 'itcm': 64*1024, 'dtcm': 128*1024, 'backup': 4*1024,
                             'd1_sram': 512*1024,
                             'd2_sram1': 128*1024, 'd2_sram2': 128*1024, 'd2_sram3': 32*1024,
                             'd3_sram': 64*1024}
            },
            {
                'name': ['45', '47', '55', '57'],
                'core': ['m4'],
                'memories': {'flash': 0, 'backup': 4*1024,
                             'd1_sram': 512*1024,
                             'd2_sram1': 128*1024, 'd2_sram2': 128*1024, 'd2_sram3': 32*1024,
                             'd3_sram': 64*1024}
            },
            {
                'name': ['a0', 'a3', 'b0', 'b3'],
                'memories': {'flash': 0, 'itcm': 64*1024, 'dtcm': 128*1024, 'backup': 4*1024,
                             'd1_sram1': 256*1024, 'd1_sram2': 384*1024, 'd1_sram3': 384*1024,
                             'd2_sram1': 64*1024, 'd2_sram2': 64*1024,
                             'd3_sram': 32*1024}
            }
        ]
    },
    'l0': {
        'start': {
            'flash': 0x08000000,
            'eeprom': 0x08080000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['10'],
                'size': ['4'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 128}
            },{
                'name': ['10'],
                'size': ['6', '8'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 256}
            },{
                # CAT1
                'name': ['10', '11', '21'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 512}
            },{
                # CAT2
                'name': ['31', '41'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 1024}
            },{
                # CAT3
                'name': ['51', '52', '53', '62', '63'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 2*1024}
            },{
                # CAT5
                'name': ['71', '72', '73', '81', '82', '83'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 6*1024}
            },
        ]
    },
    'l1': {
        'start': {
            'flash': 0x08000000,
            'eeprom': 0x08080000,
            'sram': 0x20000000
        },
        'model': [
            {
                # CAT1 & 2
                'name': ['00', '51', '52'],
                'size': ['6', '8', 'b'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 4*1024}
            },{
                # CAT3
                'name': ['00', '51', '52', '62'],
                'size': ['c'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 8*1024}
            },{
                # CAT4
                'name': ['51', '52', '62'],
                'size': ['d'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 12*1024}
            },{
                # CAT5 & 6
                'name': ['51', '52', '62'],
                'size': ['e'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 16*1024}
            },
        ]
    },
    'l4': {
        'start': {
            'flash': 0x08000000,
            'ccm': 0x10000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['12', '22'],
                'memories': {'flash': 0, 'sram1': 0, 'ccm': 8*1024}
            },{
                'name': ['51', '71', '75', '76', '85', '86'],
                'memories': {'flash': 0, 'sram1': 0, 'ccm': 32*1024}
            },{
                'name': ['31', '32', '33', '42', '43', '52', '62'],
                'memories': {'flash': 0, 'sram1': 0, 'ccm': 16*1024}
            },{
                'name': ['96', 'a6'],
                'memories': {'flash': 0, 'sram1': 0, 'ccm': 64*1024}
            },
            # Technically part of the STM32L4+ family
            {
                'name': ['r5', 'r7', 'r9', 's5', 's7', 's9'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 64*1024, 'sram3': 384*1024}
            },{
                'name': ['p5', 'q5'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 64*1024, 'sram3': 128*1024}
            }
        ]
    },
    'wb': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['10', '15'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 36*1024}
            },{
                'name': ['30', '35', '50', '55', '5m'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 64*1024}
            }
        ]
    },
    'wl': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['54', '55', 'e4', 'e5'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 32*1024}
            }
        ]
    },
}


def getMemoryModel(device_id):
    mem_fam = stm32_memory[device_id.family]
    mem_model = None
    for model in mem_fam['model']:
        if all(device_id[k] in v for k, v in model.items() if k not in ['start', 'memories']):
            mem_model = model
            break
    if mem_model == None:
        LOGGER.error("Memory model not found for device '{}'".format(device_id.string))
        exit(1)
    start = dict(mem_fam['start'])
    memories = dict(mem_model['memories'])
    start.update(mem_model.get('start', {}))
    return (start, memories)

def getMemoryForDevice(device_id, total_flash, total_ram):
    mem_start, mem_model = getMemoryModel(device_id)

    # Correct Flash size
    mem_model["flash"] = total_flash

    # Correct RAM size
    main_sram = next( (name for (name, size) in mem_model.items() if size == 0), None )
    if main_sram is not None:
        main_sram_name = next( ram for ram in mem_start.keys() if main_sram.startswith(ram) )
        # compute the size from total ram
        mem_model[main_sram] = total_ram
        main_sram_index = int(main_sram.split("sram")[-1]) if main_sram[-1].isdigit() else 0
        for name, size in mem_model.items():
            mem_index = int(name.split("sram")[-1]) if name[-1].isdigit() else 0
            if name.startswith(main_sram_name) and mem_index != main_sram_index:
                mem_model[main_sram] -= size

    # Assemble flattened memories
    memories = []
    for name, size in mem_model.items():
        sram_name = next( ram for ram in mem_start.keys() if name.startswith(ram) )
        index = int(name.split("sram")[-1]) if name[-1].isdigit() else 0
        start = mem_start[sram_name]
        if index > 1:
            # correct start address
            for mem_name, mem_size in mem_model.items():
                mem_index = int(mem_name.split("sram")[-1]) if mem_name[-1].isdigit() else 0
                if mem_name.startswith(sram_name) and mem_index < index:
                    start += mem_size
        memories.append( (name, start, size) )

    return memories


