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
                'devices': [{'family': ['f0']}]
            },{
                'hardware': 'stm32-l0',
                'features': ['oversampler', 'calfact', 'prescaler'],
                'devices': [{'family': ['l0']}]
            },{
                'hardware': 'stm32-g0',
                'features': ['oversampler', 'calfact', 'prescaler'],
                'devices': [{'family': ['g0']}]
            },{
                # F373 & F378 has a non-special ADC
                'hardware': 'stm32',
                'features': [],
                'devices': [{'family': ['f3'], 'name': ['73', '78']}]
            },{
                'hardware': 'stm32-f3',
                'features': [],
                'devices': [{'family': ['f3', 'l4', 'g4', 'wb']}]
            },{
                'hardware': 'stm32-h7',
                'features': [],
                'devices': [{'family': ['h7']}]
            },{
                'hardware': 'stm32',
                'features': [],
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
                'devices': [{'family': ['f0', 'g0', 'f1']}]
            },{
                # 28 shared filters
                'hardware': 'stm32',
                'features': ['filter-28'],
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
                'devices': '*'
            }
        ]
    }],
    'crc': [{
        'instances': '*',
        'groups': [
            {
                # Custom polynomial and reverse data
                'hardware': 'stm32',
                'features': ['polynomial', 'reverse'],
                'devices': [{'family': ['f0', 'f3', 'f7', 'h7']}]
            },{
                # Custom polynomial and reverse data
                'hardware': 'stm32',
                'features': ['reverse'],
                'devices': [{'family': ['g0', 'g4']}]
            },{
                # no poly size
                'hardware': 'stm32',
                'features': [],
                'devices': '*'
            }
        ]
    }],
    'dma': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-mux',
                'features': [],
                'devices': [{'family': ['h7', 'g0', 'g4', 'wb']}, {'family': ['l4'], 'name': ['p5', 'p7', 'p9', 'q5', 'q7', 'q9', 'r5', 'r7', 'r9', 's5', 's7', 's9']}]
            },
            {
                'hardware': 'stm32-stream-channel',
                'features': [],
                'devices': [{'family': ['f2', 'f4', 'f7']}]
            },
            {
                'hardware': 'stm32-channel-request',
                'features': [],
                'devices': [{'family': ['l0', 'l4']}, {'family': ['f0'], 'name': ['91', '98']}, {'family': ['f0'], 'name': ['30'], 'size': ['c']}]
            },
            {
                'hardware': 'stm32-channel',
                'features': [],
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
                'devices': [{'family': ['f0', 'f3', 'f7', 'g0', 'g4', 'wb']}]
            },{
                'hardware': 'stm32',
                'features': [],
                'devices': '*'
            }
        ]
    }],
    'spi': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32',
                'features': {'data-size':'SPI_CR2_DS_3', 'fifo':'SPI_SR_FRLVL'},
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
                'devices': [{'family': ['f1']}]
            },{
                'hardware': 'stm32',
                'features': ['status'],
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
                    'devices': '*'
                }
            ]
        },{
            'instances': ['2', '3', '4', '5'],
            'groups': [
                {
                    'hardware': 'stm32-general-purpose',
                    'features': [],
                    'devices': '*'
                }
            ]
        },{
            'instances': ['9', '10', '11', '12', '13', '14', '15', '16', '17'],
            'groups': [
                {
                    'hardware': 'stm32-general-purpose',
                    'features': [],
                    'devices': '*'
                }
            ]
        },{
            'instances': ['6', '7'],
            'groups': [
                {
                    'hardware': 'stm32-basic',
                    'features': [],
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
                'devices': [{'family': ['f1']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'fpu', 'ccm-wp', 'cfgr2'],
                'devices': [{'family': ['f3', 'g4']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'sram2-wp', 'cfgr2', 'imr'],
                'devices': [{'family': ['wb']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'cfgr2', 'itline'],
                'devices': [{'family': ['f0'], 'name': ['91', '98']}, {'family': ['g0']}]
            },{
                'hardware': 'stm32',
                'features': ['exti', 'cfgr2'],
                'devices': [{'family': ['f0']}]
            },{
                'hardware': 'stm32',
                'features': ['exti'],
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
                'devices': '*'
            }
        ]
    }],
    'i2c': [
        {
            # F1/F2/F4/L1 standard I2C with SMBus support
            'instances': '*',
            'groups': [
                {
                    # Some F4 have a digital noise filter
                    'hardware': 'stm32',
                    'features': ['dnf'],
                    'devices': [{'family': ['f4'], 'name': ['27', '29', '37', '39', '46', '69', '79']}]
                },{
                    'hardware': 'stm32',
                    'features': [],
                    'devices': [{'family': ['f1', 'f2', 'f4', 'l1']}]
                }
            ]
        },{
            # F0/F3/F7/L0/L4/L4+/H7 extended I2C instance 2 with optional FM+ and SMBus support
            'instances': ['2'],
            'groups': [
                {
                    # This hardware supports neither FM+ (1 Mhz) nor SMBus
                    'hardware': 'stm32-extended',
                    'features': ['dnf'],
                    'devices': [
                        {
                            'family': ['f0'],
                            'name': ['30', '31', '38', '51', '58']
                        },{
                            'family': ['f0'],
                            'name': ['70'],
                            'size': ['b']
                        }
                    ]
                },{
                    # This hardware supports FM+ (1 Mhz) but not SMBus
                    'hardware': 'stm32-extended',
                    'features': ['dnf', 'fmp'],
                    'devices': [{'family': ['f0', 'g0', 'l0']}]
                },{
                    # This hardware supports FM+ (1 Mhz) and SMBus
                    'hardware': 'stm32-extended',
                    'features': ['dnf', 'fmp'],
                    'devices': [{'family': ['f3', 'f7', 'l4', 'h7', 'g4', 'wb']}]
                }
            ]
        },{
            # F0/F3/F7/L0/L4/L4+/H7 extended I2C with FM+ and SMBus support
            'instances': ['1', '3', '4'],
            'groups': [
                {
                    # This hardware supports FM+ (1 Mhz) and SMBus
                    'hardware': 'stm32-extended',
                    'features': ['dnf', 'fmp'],
                    'devices': [{'family': ['f0', 'g0', 'f3', 'f7', 'l0', 'l4', 'h7', 'g4', 'wb']}]
                }
            ]
        }
    ],
    'uart': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-extended',
                'features': {'swap': 'USART_CR2_SWAP', 'over8': 'USART_CR1_OVER8', 'half-duplex': 'USART_CR3_HDSEL', '7-bit': 'USART_CR1_M1', 'tcbgt': 'USART_CR1_RXNEIE_RXFNEIE'},
                'devices': [{'family': ['f0', 'f3', 'f7', 'l4', 'g0', 'g4', 'wb']}]
            },{
                'hardware': 'stm32',
                'features': {'swap': 'USART_CR2_SWAP', 'over8': 'USART_CR1_OVER8', 'half-duplex': 'USART_CR3_HDSEL', '7-bit': 'USART_CR1_M1', 'tcbgt': 'USART_CR1_RXNEIE_RXFNEIE'},
                'devices': '*'
            }
        ]
    }],
    'usart': [{
        'instances': '*',
        'groups': [
            {
                'hardware': 'stm32-extended',
                'features': {'swap': 'USART_CR2_SWAP', 'over8': 'USART_CR1_OVER8', 'half-duplex': 'USART_CR3_HDSEL', '7-bit': 'USART_CR1_M1', 'tcbgt': 'USART_CR1_RXNEIE_RXFNEIE'},
                'devices': [{'family': ['f0', 'f3', 'f7', 'l4', 'g0', 'g4', 'wb']}]
            },{
                'hardware': 'stm32',
                'features': {'swap': 'USART_CR2_SWAP', 'over8': 'USART_CR1_OVER8', 'half-duplex': 'USART_CR3_HDSEL', '7-bit': 'USART_CR1_M1', 'tcbgt': 'USART_CR1_RXNEIE_RXFNEIE'},
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
                'devices': [{'family': ['f1']}]
            },{
                # The rest remaps pins individually
                'hardware': 'stm32',
                'features': [],
                'devices': '*'
            }
        ]
    }]
}

def resolvePeripheralFeatures(header, feature_map, module):
    if isinstance(feature_map, list):
        return []

    name, instance, version = module
    features = set()
    for feature, registers in feature_map.items():
        if not isinstance(registers, list): registers = [registers];
        if any(r.format(n=name, i=instance) in header.get_filtered_defines() for r in registers):
            features.add(feature)

    return list(features)

def getPeripheralData(did, module, header):
    name, inst, version = module
    if name in stm_peripherals:
        for instance_list in stm_peripherals[name]:
            if instance_list['instances'] == '*' or inst[len(name):] in instance_list['instances']:
                for group in instance_list['groups']:
                    if group['devices'] == '*' or DeviceMerger._get_index_for_id(group['devices'], did) >= 0:
                        return (group['hardware'], resolvePeripheralFeatures(header, group['features'], module))

    return ('stm32-' + version, [])
