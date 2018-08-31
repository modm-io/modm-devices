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

stm32f1_remaps = \
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

def getRemapForModuleConfig(module, config):
    mmm = {}
    if module in stm32f1_remaps:
        mmm['mask'] = stm32f1_remaps[module]['mask']
        mmm['position'] = stm32f1_remaps[module]['position']
        mmm['mapping'] = stm32f1_remaps[module]['mapping'][int(config)]
    return mmm

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
                'name': ['03x6', '03x8', '28', '34'],
                'memories': {'flash': 0, 'ccm': 4*1024, 'sram1': 0}
            },
            {
                'name': ['03xb', '03xc', '58'],
                'memories': {'flash': 0, 'ccm': 8*1024, 'sram1': 0}
            },
            {
                'name': ['03xd', '03xe', '98'],
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
            'flash': 0x08000000,
            'dtcm': 0x20000000,
            'itcm': 0x00000000,
            'sram': 0x20010000,
            'backup': 0x40024000
        },
        'model': [
            {
                'name': ['22', '32', '23', '30', '33', '45', '46', '50', '56', '65', '67', '68', '69', '77', '78', '79'],
                'memories': {'flash': 0, 'itcm': 16*1024, 'dtcm': 64*1024, 'sram1': 0, 'sram2': 16*1024, 'backup': 4*1024}
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
                # CAT1
                'name': ['11', '21'],
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
                'name': ['00x6', '00x8', '00xb', '51x6', '51x8', '51xb', '52x6', '52x8', '52xb'],
                'size': ['6', '8', 'b'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 4*1024}
            },{
                # CAT3
                'name': ['00xc', '51xc', '52xc', '62xc'],
                'size': ['c'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 8*1024}
            },{
                # CAT4
                'name': ['51xd', '52xd', '62xd'],
                'size': ['d'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 12*1024}
            },{
                # CAT5 & 6
                'name': ['51xe', '52xe', '62xe'],
                'size': ['e'],
                'memories': {'flash': 0, 'sram1': 0, 'eeprom': 16*1024}
            },
        ]
    },
    'l4': {
        'start': {
            'flash': 0x08000000,
            'eeprom': 0x08080000,
            'sram3': 0x20030000,
            'sram2': 0x10000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'name': ['31', '33', '43', '51', '71', '75', '76', '85', '86', '96', 'a6'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 32*1024}
            },{
                'name': ['32', '42', '52', '62'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 16*1024}
            },{
                'name': ['r5', 'r7', 'r9', 's5', 's7', 's9'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 64*1024, 'sram3': 384*1024}
            },
        ]
    },
}

def getMemoryForDevice(device_id):
    mem_fam = stm32_memory[device_id.family]
    mem_model = None
    for model in mem_fam['model']:
        if any(name.startswith(device_id.name) for name in model['name']):
            if device_id.name in model['name']:
                mem_model = model
                break
            elif "{}x{}".format(device_id.name, device_id.size) in model['name']:
                mem_model = model
                break
    if mem_model == None:
        LOGGER.error("Memory model not found for device '{}'".format(device_id.string))
        exit(1)
    return (mem_fam['start'], mem_model['memories'])
