# -*- coding: utf-8 -*-
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

stm_groups = \
[
    # STM32F0 devices
    {
        'family': ['f0'],
        'name': ['30', '70'],
        'size': ['4', '6']
    },{
        'family': ['f0'],
        'name': ['30', '70'],
        'size': ['8']
    },{
        'family': ['f0'],
        'name': ['30', '70'],
        'size': ['b', 'c']
    },{
        'family': ['f0'],
        'name': ['31', '51'],
        'size': ['4', '6']
    },{
        'family': ['f0'],
        'name': ['51', '71'],
        'size': ['8']
    },{
        'family': ['f0'],
        'name': ['71', '91'],
        'size': ['b', 'c']
    },{
        'family': ['f0'],
        'name': ['42'],
        'size': ['4', '6']
    },{
        'family': ['f0'],
        'name': ['72'],
        'size': ['8', 'b']
    },{
        'family': ['f0'],
        'name': ['38', '48'],
        'size': ['4', '6']
    },{
        'family': ['f0'],
        'name': ['58'],
        'size': ['8']
    },{
        'family': ['f0'],
        'name': ['78', '98'],
        'size': ['b', 'c']
    },

    # STM32F1 devices
    {
        'family': ['f1'],
        'name': ['00'],
        'size': ['4', '6']
    },{
        'family': ['f1'],
        'name': ['00'],
        'size': ['8', 'b']
    },{
        'family': ['f1'],
        'name': ['00'],
        'size': ['c', 'd', 'e']
    },{
        'family': ['f1'],
        'name': ['01', '02'],
        'size': ['4', '6']
    },{
        'family': ['f1'],
        'name': ['01', '02'],
        'size': ['8', 'b']
    },{
        'family': ['f1'],
        'name': ['01'],
        'size': ['c', 'd', 'e']
    },{
        'family': ['f1'],
        'name': ['01'],
        'size': ['f', 'g']
    },{
        'family': ['f1'],
        'name': ['03'],
        'size': ['4', '6']
    },{
        'family': ['f1'],
        'name': ['03'],
        'size': ['8', 'b']
    },{
        'family': ['f1'],
        'name': ['03'],
        'size': ['c', 'd', 'e']
    },{
        'family': ['f1'],
        'name': ['03'],
        'size': ['f', 'g']
    },{
        'family': ['f1'],
        'name': ['05', '07']
    },

    # STM32F2 devices
    {
        'family': ['f2'],
        'name': ['05']
    },{
        'family': ['f2'],
        'name': ['07', '15', '17']
    },

    # STM32F3 devices
    {
        'family': ['f3'],
        'name': ['01']
    },{
        'family': ['f3'],
        'name': ['02'],
        'size': ['6', '8']
    },{
        'family': ['f3'],
        'name': ['02'],
        'size': ['b', 'c', 'd', 'e']
    },{
        'family': ['f3'],
        'name': ['03'],
        'size': ['6', '8']
    },{
        'family': ['f3'],
        'name': ['03'],
        'size': ['b', 'c', 'd', 'e']
    },{
        'family': ['f3'],
        'name': ['18', '28']
    },{
        'family': ['f3'],
        'name': ['34']
    },{
        'family': ['f3'],
        'name': ['58', '98']
    },{
        'family': ['f3'],
        'name': ['73', '78']
    },

    # STM32F4 devices
    {
        'family': ['f4'],
        'name': ['01', '11']
    },{
        'family': ['f4'],
        'name': ['05', '07', '15', '17']
    },{
        'family': ['f4'],
        'name': ['10']
    },{
        'family': ['f4'],
        'name': ['12']
    },{
        'family': ['f4'],
        'name': ['13', '23']
    },{
        'family': ['f4'],
        'name': ['27', '29', '37', '39']
    },{
        'family': ['f4'],
        'name': ['46']
    },{
        'family': ['f4'],
        'name': ['69', '79']
    },

    # STM32F7 devices
    {
        'family': ['f7'],
        'name': ['22', '32', '23', '33']
    },{
        'family': ['f7'],
        'name': ['30', '50']
    },{
        'family': ['f7'],
        'name': ['45', '46', '56']
    },{
        'family': ['f7'],
        'name': ['65', '67', '68', '69', '77', '78', '79']
    },

    # STM32H7 devices
    {
        'family': ['h7'],
        'name': ['43', '53']
    },{
        'family': ['h7'],
        'name': ['50']
    },

    # STM32L0 devices
    {
        'family': ['l0'],
        'name': ['10']
    },{
        'family': ['l0'],
        'name': ['11', '21']
    },{
        'family': ['l0'],
        'name': ['31', '41']
    },{
        'family': ['l0'],
        'name': ['51', '52', '62', '53', '63']
    },{
        'family': ['l0'],
        'name': ['71', '81', '72', '82', '73', '83']
    },

    # STM32L1 devices
    {
        'family': ['l1'],
        'name': ['00']
    },{
        'family': ['l1'],
        'name': ['51', '52'],
        'size': ['6', '8', 'b']
    },{
        'family': ['l1'],
        'name': ['51', '52', '62'],
        'size': ['c', 'd', 'e']
    },

    # STM32L4 devices
    {
        'family': ['l4'],
        'name': ['12', '22']
    },{
        'family': ['l4'],
        'name': ['51', '71']
    },{
        'family': ['l4'],
        'name': ['32', '42']
    },{
        'family': ['l4'],
        'name': ['52', '62']
    },{
        'family': ['l4'],
        'name': ['31', '33', '43']
    },{
        'family': ['l4'],
        'name': ['75', '85']
    },{
        'family': ['l4'],
        'name': ['76', '86']
    },{
        'family': ['l4'],
        'name': ['96', 'a6']
    },

    # STM32L4+ devices
    {
        'family': ['l4'],
        'name': ['r5', 'r7', 'r9']
    },{
        'family': ['l4'],
        'name': ['s5', 's7', 's9']
    },
]
