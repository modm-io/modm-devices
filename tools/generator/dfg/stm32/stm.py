# -*- coding: utf-8 -*-
# Copyright (c) 2015-2016, Niklas Hauser
# All rights reserved.

import logging

LOGGER = logging.getLogger("dfg.stm.data")

stm32_defines = \
{
    'f0': [
        'STM32F030x6',  # STM32F030x4, STM32F030x6 Devices (STM32F030xx microcontrollers where the Flash memory ranges between 16 and 32 Kbytes)
        'STM32F030x8',  # STM32F030x8 Devices (STM32F030xx microcontrollers where the Flash memory is 64 Kbytes)
        'STM32F031x6',  # STM32F031x4, STM32F031x6 Devices (STM32F031xx microcontrollers where the Flash memory ranges between 16 and 32 Kbytes)
        'STM32F038xx',  # STM32F038xx Devices (STM32F038xx microcontrollers where the Flash memory is 32 Kbytes)
        'STM32F042x6',  # STM32F042x4, STM32F042x6 Devices (STM32F042xx microcontrollers where the Flash memory ranges between 16 and 32 Kbytes)
        'STM32F048xx',  # STM32F048xx Devices (STM32F042xx microcontrollers where the Flash memory is 32 Kbytes)
        'STM32F051x8',  # STM32F051x4, STM32F051x6, STM32F051x8 Devices (STM32F051xx microcontrollers where the Flash memory ranges between 16 and 64 Kbytes)
        'STM32F058xx',  # STM32F058xx Devices (STM32F058xx microcontrollers where the Flash memory is 64 Kbytes)
        'STM32F070x6',  # STM32F070x6 Devices (STM32F070x6 microcontrollers where the Flash memory ranges between 16 and 32 Kbytes)
        'STM32F070xB',  # STM32F070xB Devices (STM32F070xB microcontrollers where the Flash memory ranges between 64 and 128 Kbytes)
        'STM32F071xB',  # STM32F071x8, STM32F071xB Devices (STM32F071xx microcontrollers where the Flash memory ranges between 64 and 128 Kbytes)
        'STM32F072xB',  # STM32F072x8, STM32F072xB Devices (STM32F072xx microcontrollers where the Flash memory ranges between 64 and 128 Kbytes)
        'STM32F078xx',  # STM32F078xx Devices (STM32F078xx microcontrollers where the Flash memory is 128 Kbytes)
        'STM32F030xC',  # STM32F030xC Devices (STM32F030xC microcontrollers where the Flash memory is 256 Kbytes)
        'STM32F091xC',  # STM32F091xC Devices (STM32F091xx microcontrollers where the Flash memory is 256 Kbytes)
        'STM32F098xx',  # STM32F098xx Devices (STM32F098xx microcontrollers where the Flash memory is 256 Kbytes)
    ],
    'f1': [
         'STM32F100xB', # STM32F100C4, STM32F100R4, STM32F100C6, STM32F100R6, STM32F100C8, STM32F100R8, STM32F100V8, STM32F100CB, STM32F100RB and STM32F100VB
         'STM32F100xE', # STM32F100RC, STM32F100VC, STM32F100ZC, STM32F100RD, STM32F100VD, STM32F100ZD, STM32F100RE, STM32F100VE and STM32F100ZE
         'STM32F101x6', # STM32F101C4, STM32F101R4, STM32F101T4, STM32F101C6, STM32F101R6 and STM32F101T6 Devices
         'STM32F101xB', # STM32F101C8, STM32F101R8, STM32F101T8, STM32F101V8, STM32F101CB, STM32F101RB, STM32F101TB and STM32F101VB
         'STM32F101xE', # STM32F101RC, STM32F101VC, STM32F101ZC, STM32F101RD, STM32F101VD, STM32F101ZD, STM32F101RE, STM32F101VE and STM32F101ZE
         'STM32F101xG', # STM32F101RF, STM32F101VF, STM32F101ZF, STM32F101RG, STM32F101VG and STM32F101ZG
         'STM32F102x6', # STM32F102C4, STM32F102R4, STM32F102C6 and STM32F102R6
         'STM32F102xB', # STM32F102C8, STM32F102R8, STM32F102CB and STM32F102RB
         'STM32F103x6', # STM32F103C4, STM32F103R4, STM32F103T4, STM32F103C6, STM32F103R6 and STM32F103T6
         'STM32F103xB', # STM32F103C8, STM32F103R8, STM32F103T8, STM32F103V8, STM32F103CB, STM32F103RB, STM32F103TB and STM32F103VB
         'STM32F103xE', # STM32F103RC, STM32F103VC, STM32F103ZC, STM32F103RD, STM32F103VD, STM32F103ZD, STM32F103RE, STM32F103VE and STM32F103ZE
         'STM32F103xG', # STM32F103RF, STM32F103VF, STM32F103ZF, STM32F103RG, STM32F103VG and STM32F103ZG
         'STM32F105xC', # STM32F105R8, STM32F105V8, STM32F105RB, STM32F105VB, STM32F105RC and STM32F105VC
         'STM32F107xC', # STM32F107RB, STM32F107VB, STM32F107RC and STM32F107VC
    ],
    'f2': [
        'STM32F205xx',
        'STM32F215xx',
        'STM32F207xx',
        'STM32F217xx',
    ],
    'f3': [
        'STM32F301x8',  # STM32F301K6, STM32F301K8, STM32F301C6, STM32F301C8, STM32F301R6 and STM32F301R8 Devices
        'STM32F302x8',  # STM32F302K6, STM32F302K8, STM32F302C6, STM32F302C8, STM32F302R6 and STM32F302R8 Devices
        'STM32F302xC',  # STM32F302CB, STM32F302CC, STM32F302RB, STM32F302RC, STM32F302VB and STM32F302VC Devices
        'STM32F302xE',  # STM32F302CE, STM32F302RE, and STM32F302VE Devices
        'STM32F303x8',  # STM32F303K6, STM32F303K8, STM32F303C6, STM32F303C8, STM32F303R6 and STM32F303R8 Devices
        'STM32F303xC',  # STM32F303CB, STM32F303CC, STM32F303RB, STM32F303RC, STM32F303VB and STM32F303VC Devices
        'STM32F303xE',  # STM32F303RE, STM32F303VE and STM32F303ZE Devices
        'STM32F373xC',  # STM32F373C8, STM32F373CB, STM32F373CC, STM32F373R8, STM32F373RB, STM32F373RC, STM32F373V8, STM32F373VB and STM32F373VC Devices
        'STM32F334x8',  # STM32F334C4, STM32F334C6, STM32F334C8, STM32F334R4, STM32F334R6 and STM32F334R8 Devices
        'STM32F318xx',  # STM32F318K8, STM32F318C8: STM32F301x8 with regulator off: STM32F318xx Devices
        'STM32F328xx',  # STM32F328C8, STM32F328R8: STM32F334x8 with regulator off: STM32F328xx Devices
        'STM32F358xx',  # STM32F358CC, STM32F358RC, STM32F358VC: STM32F303xC with regulator off: STM32F358xx Devices
        'STM32F378xx',  # STM32F378CC, STM32F378RC, STM32F378VC: STM32F373xC with regulator off: STM32F378xx Devices
        'STM32F398xx',  # STM32F398CE, STM32F398RE, STM32F398VE: STM32F303xE with regulator off: STM32F398xx Devices
    ],
    'f4': [
        'STM32F405xx',  # STM32F405RG, STM32F405VG and STM32F405ZG Devices
        'STM32F415xx',  # STM32F415RG, STM32F415VG and STM32F415ZG Devices
        'STM32F407xx',  # STM32F407VG, STM32F407VE, STM32F407ZG, STM32F407ZE, STM32F407IG and STM32F407IE Devices
        'STM32F417xx',  # STM32F417VG, STM32F417VE, STM32F417ZG, STM32F417ZE, STM32F417IG and STM32F417IE Devices
        'STM32F427xx',  # STM32F427VG, STM32F427VI, STM32F427ZG, STM32F427ZI, STM32F427IG and STM32F427II Devices
        'STM32F437xx',  # STM32F437VG, STM32F437VI, STM32F437ZG, STM32F437ZI, STM32F437IG and STM32F437II Devices
        'STM32F429xx',  # STM32F429VG, STM32F429VI, STM32F429ZG, STM32F429ZI, STM32F429BG, STM32F429BI, STM32F429NG, STM32F439NI, STM32F429IG and STM32F429II Devices
        'STM32F439xx',  # STM32F439VG, STM32F439VI, STM32F439ZG, STM32F439ZI, STM32F439BG, STM32F439BI, STM32F439NG, STM32F439NI, STM32F439IG and STM32F439II Devices
        'STM32F401xC',  # STM32F401CB, STM32F401CC, STM32F401RB, STM32F401RC, STM32F401VB and STM32F401VC Devices
        'STM32F401xE',  # STM32F401CD, STM32F401RD, STM32F401VD, STM32F401CE, STM32F401RE and STM32F401VE Devices
        'STM32F410Tx',  # STM32F410T8 and STM32F410TB Devices
        'STM32F410Cx',  # STM32F410C8 and STM32F410CB Devices
        'STM32F410Rx',  # STM32F410R8 and STM32F410RB Devices
        'STM32F411xE',  # STM32F411CD, STM32F411RD, STM32F411VD, STM32F411CE, STM32F411RE and STM32F411VE Devices
        'STM32F446xx',  # STM32F446MC, STM32F446ME, STM32F446RC, STM32F446RE, STM32F446VC, STM32F446VE, STM32F446ZC and STM32F446ZE Devices
        'STM32F469xx',  # STM32F469AI, STM32F469II, STM32F469BI, STM32F469NI, STM32F469AG, STM32F469IG, STM32F469BG, STM32F469NG, STM32F469AE, STM32F469IE, STM32F469BE and STM32F469NE Devices
        'STM32F479xx',  # STM32F479AI, STM32F479II, STM32F479BI, STM32F479NI, STM32F479AG, STM32F479IG, STM32F479BG and STM32F479NG Devices
        'STM32F412Cx',  # STM32F412CEU and STM32F412CGU Devices
        'STM32F412Zx',  # STM32F412ZET, STM32F412ZGT, STM32F412ZEJ and STM32F412ZGJ Devices
        'STM32F412Vx',  # STM32F412VET, STM32F412VGT, STM32F412VEH and STM32F412VGH Devices
        'STM32F412Rx',  # STM32F412RET, STM32F412RGT, STM32F412REY and STM32F412RGY Devices
    ],
    'f7': [
        'STM32F756xx',  # STM32F756VG, STM32F756ZG, STM32F756ZG, STM32F756IG, STM32F756BG and STM32F756NG Devices
        'STM32F746xx',  # STM32F746VE, STM32F746VG, STM32F746ZE, STM32F746ZG, STM32F746IE, STM32F746IG, STM32F746BE, STM32F746BG, STM32F746NE and STM32F746NG Devices
        'STM32F745xx',  # STM32F745VE, STM32F745VG, STM32F745ZG, STM32F745ZE, STM32F745IE and STM32F745IG Devices
        'STM32F765xx',  # STM32F765BI, STM32F765BG, STM32F765NI, STM32F765NG, STM32F765II, STM32F765IG, STM32F765ZI, STM32F765ZG, STM32F765VI, STM32F765VG Devices
        'STM32F767xx',  # STM32F767BG, STM32F767BI, STM32F767IG, STM32F767II, STM32F767NG, STM32F767NI, STM32F767VG, STM32F767VI, STM32F767ZG, STM32F767ZI Devices
# The STM32F768 devices use the F767 header file.
#       'STM32F767xx',  # STM32F768AI Devices
        'STM32F769xx',  # STM32F769AG, STM32F769AI, STM32F769BG, STM32F769BI, STM32F769IG, STM32F769II, STM32F769NG, STM32F769NI Devices
        'STM32F777xx',  # STM32F777VI, STM32F777ZI, STM32F777II, STM32F777BI, STM32F777NI Devices
# The STM32F778 devices use the F777 header file.
#       'STM32F777xx',  # STM32F778AI Devices
        'STM32F779xx',  # STM32F779II, STM32F779BI, STM32F779NI, STM32F779AI Devices
    ]
}

def getDefineForDevice(device_id):
    if device_id["family"] not in stm32_defines:
        return None
    # get the defines for this device family
    familyDefines = stm32_defines[device_id["family"]]
    # get all defines for this device name
    devName = 'STM32F{}'.format(device_id["name"])

    # Map STM32F7x8 -> STM32F7x7
    if device_id["family"] == 'f7' and devName[8] == '8':
        devName = devName[:8] + '7'

    deviceDefines = sorted([define for define in familyDefines if define.startswith(devName)])
    # if there is only one define thats the one
    if len(deviceDefines) == 1:
        return deviceDefines[0]

    # now we match for the size-id.
    devNameMatch = devName + 'x{}'.format(device_id["size"].upper())
    for define in deviceDefines:
        if devNameMatch <= define:
            return define

    # now we match for the pin-id.
    devNameMatch = devName + '{}x'.format(device_id["pin"].upper())
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

stm32_memory = \
{
    'f0': {
        'start': {
            'flash': 0x08000000,
            'sram': 0x20000000
        },
        'model': [
            {
                'names': ['030', '031', '038', '042', '048', '051', '058', '070', '071', '072', '078', '091', '098'],
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
                'names': ['100', '101', '102', '103', '105', '107'],
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
                'names': ['205', '207', '215', '217'],
                'memories': {'flash': 0, 'sram1': 0, 'sram2': 16}
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
                'names' : ['301', '302', '318', '378', '373'],
                'memories' : {'flash': 0, 'sram1' : 0}
            },
            {
                'names': ['303x6', '303x8', '328', '334'],
                'memories': {'flash': 0, 'ccm': 4, 'sram1': 0}
            },
            {
                'names': ['303xb', '303xc', '358'],
                'memories': {'flash': 0, 'ccm': 8, 'sram1': 0}
            },
            {
                'names': ['303xd', '303xe', '398'],
                'memories': {'flash': 0, 'ccm': 16, 'sram1': 0}
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
                'names' : ['401', '410', '411', '412', '446'],
                'memories' : {'flash': 0, 'sram1' : 0}
            },
            {
                'names': ['405', '407', '415', '417'],
                'memories': {'flash': 0, 'ccm': 64, 'sram1': 0, 'sram2': 16, 'backup': 4}
            },
            {
                'names': ['427', '429', '437', '439'],
                'memories': {'flash': 0, 'ccm': 64, 'sram1': 0, 'sram2': 16, 'sram3': 64, 'backup': 4}
            },
            {
                'names': ['469', '479'],
                'memories': {'flash': 0, 'ccm': 64, 'sram1': 0, 'sram2': 32, 'sram3': 128, 'backup': 4}
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
                'names': ['745', '746', '756', '765', '767', '768', '769', '777', '778', '779'],
                'memories': {'flash': 0, 'itcm': 16, 'dtcm': 64, 'sram1': 0, 'sram2': 16, 'backup': 4}
            }
        ]
    }
}

def getMemoryForDevice(device_id):
    mem_fam = stm32_memory[device_id["family"]]
    mem_model = None
    for model in mem_fam['model']:
        if any(name.startswith(device_id["name"]) for name in model['names']):
            if device_id["name"] in model['names']:
                mem_model = model
                break
            elif "{}x{}".format(device_id["name"], device_id["size"]) in model['names']:
                mem_model = model
                break
    if mem_model == None:
        LOGGER.error("Memory model not found for device '{}'".format(device_id.string))
        exit(1)
    return (mem_fam['start'], mem_model['memories'])
