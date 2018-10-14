# -*- coding: utf-8 -*-
# Copyright (c) 2017, Niklas Hauser
# All rights reserved.

from ..merger import DeviceMerger

stm_peripherals = \
{
    'adc': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-f0',
                'features': [],
                'protocols': ['analog-in'],
                'devices': [{'family': ['f0']}]
            },{
                'hardware': 'stm32-f0',
                'features': ['oversampler', 'calfact', 'prescaler'],
                'protocols': ['analog-in'],
                'devices': [{'family': ['l0']}]
            },{
                # F373 & F378 has a non-special ADC
                'hardware': 'stm32',
                'features': [],
                'protocols': ['analog-in'],
                'devices': [{'family': ['f3'], 'name': ['73', '78']}]
            },{
                'hardware': 'stm32-f3',
                'features': [],
                'protocols': ['analog-in'],
                'devices': [{'family': ['f3', 'l4']}]
            },{
                'hardware': 'stm32-h7',
                'features': [],
                'protocols': ['analog-in'],
                'devices': [{'family': ['h7']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': ['analog-in'],
                'devices': '*'
            }
        ]
    }],
    'sdadc': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-f3',
                'features': [],
                'protocols': ['analog-in'],
                'devices': [{'family': ['f3']}]
            }
        ]
    }],
    'can': [{
        'instances': '*',
        'groups': [
            {
                # 14 shared filters
                'hardware': 'stm32',
                'features': ['filter-14'],
                'protocols': ['can-v2.0a', 'can-v2.0b'],
                'devices': [{'family': ['f0', 'f1']}]
            },{
                # 28 shared filters
                'hardware': 'stm32',
                'features': ['filter-28'],
                'protocols': ['can-v2.0a', 'can-v2.0b'],
                'devices': '*'
            }
        ]
    }],
    'fdcan': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'crc': [{
        'instances': '*',
        'groups': [
            {
                # Custom polynomial and reserve data
                'hardware': 'stm32',
                'features': ['polynomial', 'reserve'],
                'protocols': ['crc32'],
                'devices': [{'family': ['f0', 'f3', 'f7', 'h7']}]
            },{
                # no poly size
                'hardware': 'stm32',
                'features': [],
                'protocols': ['crc32'],
                'devices': '*'
            }
        ]
    }],
    'dma': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': ['mem2mem', 'mem2per', 'per2per'],
                'devices': [{'family': ['f0', 'f1', 'f3']}]
            },{
                'hardware': 'stm32-extended',
                'features': [],
                'protocols': ['mem2mem', 'mem2per', 'per2per'],
                'devices': '*'
            }
        ]
    }],
    'iwdg': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': ['window'],
                'protocols': [],
                'devices': [{'family': ['f0', 'f3', 'f7']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'spi': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': ['data-size', 'nss-pulse', 'fifo'],
                'protocols': [],
                'devices': [{'family': ['f0', 'f3', 'f7', 'l4']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'dac': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': [{'family': ['f1']}]
            },{
                'hardware': 'stm32',
                'features': ['status'],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'dcmi': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'dsi': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'sdio': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'tim': [
        {
            'instances': ['1', '8', '20'],
            'groups': [
                {
                    'hardware': 'stm32-advanced',
                    'features': [],
                    'protocols': [],
                    'devices': '*'
                }
            ]
        },{
            'instances': ['2', '3', '4', '5'],
            'groups': [
                {
                    'hardware': 'stm32-general-purpose',
                    'features': [],
                    'protocols': [],
                    'devices': '*'
                }
            ]
        },{
            'instances': ['9', '10', '11', '12', '13', '14', '15', '16', '17'],
            'groups': [
                {
                    'hardware': 'stm32-general-purpose',
                    'features': [],
                    'protocols': [],
                    'devices': '*'
                }
            ]
        },{
            'instances': ['6', '7'],
            'groups': [
                {
                    'hardware': 'stm32-basic',
                    'features': [],
                    'protocols': [],
                    'devices': '*'
                }
            ]
        }
    ],
    'sys': [{
        'instances': '*',
        'groups': [
            {
                # Registers are called AFIO, not SYS!
                'hardware': 'stm32-f1',
                'features': ['exti', 'remap'],
                'protocols': [],
                'devices': [{'family': ['f1']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'fpu', 'ccm-wp', 'cfgr2'],
                'protocols': [],
                'devices': [{'family': ['f3']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'cfgr2', 'itline'],
                'protocols': [],
                'devices': [{'family': ['f0'], 'name': ['91', '98']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'cfgr2'],
                'protocols': [],
                'devices': [{'family': ['f0']}]
            },{
                'hardware': 'stm32',
                'features': ['exti'],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'dma2d': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': ['2d', 'blitter'],
                'devices': '*'
            }
        ]
    }],
    'rng': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': [],
                'protocols': [],
                'devices': '*'
            }
        ]
    }],
    'i2c': [{
        'instances': '*',
        'groups': [
            {
                # Some F4 have a digital noise filter
                'hardware': 'stm32',
                'features': ['dnf'],
                'protocols': ['i2c-v3.0', 'smb-v2.0', 'pmb-v1.1'],
                'devices': [{'family': ['f4'], 'name': ['27', '29', '37', '39', '46', '69', '79']}]
            },{
                'hardware': 'stm32-extended',
                'features': ['dnf'],
                'protocols': ['i2c-v3.0', 'smb-v2.0', 'pmb-v1.1'],
                'devices': [{'family': ['f0', 'f3', 'f7', 'l4']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': ['i2c-v3.0', 'smb-v2.0', 'pmb-v1.1'],
                'devices': '*'
            }
        ]
    }],
    'uart': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-extended',
                'features': ['wakeup'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f0', 'f3']}]
            },{
                'hardware': 'stm32-extended',
                'features': ['tcbgt'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['l4'], 'name': ['r5', 'r7', 'r9', 's5', 's7', 's9']}]
            },{
                'hardware': 'stm32-extended',
                'features': [],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f7', 'l4']}]
            },{
                'hardware': 'stm32',
                'features': ['over8'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f2', 'f4']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': ['uart', 'spi'],
                'devices': '*'
            }
        ]
    }],
    'usart': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-extended',
                'features': ['wakeup'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f0', 'f3']}]
            },{
                'hardware': 'stm32-extended',
                'features': ['tcbgt'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['l4'], 'name': ['r5', 'r7', 'r9', 's5', 's7', 's9']}]
            },{
                'hardware': 'stm32-extended',
                'features': [],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f7', 'l4']}]
            },{
                'hardware': 'stm32',
                'features': ['over8'],
                'protocols': ['uart', 'spi'],
                'devices': [{'family': ['f2', 'f4']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'protocols': ['uart', 'spi'],
                'devices': '*'
            }
        ]
    }],
    'gpio': [{
        'instances': '*',
        'groups': [
            {
                # The F1 remaps groups of pins
                'hardware': 'stm32-f1',
                'features': [],
                'protocols': ['digital-in', 'digital-out', 'open-drain', 'exti'],
                'devices': [{'family': ['f1']}]
            },{
                # The rest remaps pins individually
                'hardware': 'stm32',
                'features': [],
                'protocols': ['digital-in', 'digital-out', 'open-drain', 'exti'],
                'devices': '*'
            }
        ]
    }]
}

def getPeripheralData(did, module):
    name, inst, version = module
    if name in stm_peripherals:
        for instance_list in stm_peripherals[name]:
            if instance_list['instances'] == '*' or inst[len(name):] in instance_list['instances']:
                for group in instance_list['groups']:
                    if group['devices'] == '*' or DeviceMerger._get_index_for_id(group['devices'], did) >= 0:
                        return (group['hardware'], group['features'], group['protocols'])

    return ('stm32-' + version, [], [])
