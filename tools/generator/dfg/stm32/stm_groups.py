# -*- coding: utf-8 -*-
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

stm_groups = \
[
    # STM32C0 devices
    {
        'family': ['c0'],
        'name': ['11', '31']
    },{
        'family': ['c0'],
        'name': ['51', '71']
    },

    # STM32F0 devices
    {
        'family': ['f0'],
        'name': ['30'],
    },{
        'family': ['f0'],
        'name': ['70'],
    },

    # STM32F1 devices
    # STM32F2 devices
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
        'name': ['58', '98']
    },

    # STM32F4 devices
    {
        'family': ['f4'],
        'name': ['01', '11']
    },

    # STM32F7 devices
    {
        'family': ['f7'],
        'name': ['65']
    },{
        'family': ['f7'],
        'name': ['69', '79']
    },
    # STM32G0 devices
    {
        'family': ['g0'],
        'name': ['70', 'b0']
    },{
        'family': ['g0'],
        'name': ['71', '81']
    },

    # STM32G4 devices
    {
        'family': ['g4'],
        'name': ['11']
    },{
        'family': ['g4'],
        'name': ['14']
    },{
        'family': ['g4'],
        'name': ['71']
    },{
        'family': ['g4'],
        'name': ['73', '83']
    },{
        'family': ['g4'],
        'name': ['74', '84']
    },

    # STM32H5 devices
    {
        'family': ['h5'],
        'name': ['e4', 'e5', 'f4', 'f5'],
        'variant': ['']
    },{
        'family': ['h5'],
        'name': ['e4', 'e5', 'f4', 'f5'],
        'variant': ['q']
    },

    # STM32H7 devices
    {
        'family': ['h7'],
        'name': ['25', '35']
    },{
        'family': ['h7'],
        'name': ['45', '55', '47', '57']
    },{
        'family': ['h7'],
        'name': ['a0', 'b0', 'a3', 'b3'],
        'variant': ['']
    },{
        'family': ['h7'],
        'name': ['a0', 'b0', 'a3', 'b3'],
        'variant': ['q']
    },{
        'family': ['h7'],
        'name': ['r3', 's3']
    },{
        'family': ['h7'],
        'name': ['r7', 's7']
    },

    # STM32L0 devices
    {
        'family': ['l0'],
        'name': ['10']
    },

    # STM32L1 devices
    {
        'family': ['l1'],
        'name': ['00']
    },{
        'family': ['l1'],
        'name': ['51', '52'],
        'size': ['6', '8', 'b']
    },

    # STM32L4 devices
    {
        'family': ['l4'],
        'name': ['51', '71']
    },{
        'family': ['l4'],
        'name': ['32', '42']
    },{
        'family': ['l4'],
        'name': ['76', '86']
    },

    # STM32L4+ devices
    {
        'family': ['l4'],
        'name': ['r5', 'r7', 'r9']
    },{
        'family': ['l4'],
        'name': ['s5', 's7', 's9']
    },{
        'family': ['l4'],
        'name': ['p5']
    },{
        'family': ['l4'],
        'name': ['q5']
    },

    # STM32L5 devices
    # STM32U0 devices
    # STM32U3 devices
    {
        'family': ['u3'],
        'name': ['b5', 'c5'],
        'variant': ['']
    },{
        'family': ['u3'],
        'name': ['b5', 'c5'],
        'variant': ['q']
    },

    # STM32U5 devices
    {
        'family': ['u5'],
        'name': ['95', '99', 'a5', 'a9'],
        'variant': ['']
    },{
        'family': ['u5'],
        'name': ['95', '99', 'a5', 'a9'],
        'variant': ['q']
    },{
        'family': ['u5'],
        'name': ['f7', 'f9', 'g7', 'g9'],
        'variant': ['']
    },{
        'family': ['u5'],
        'name': ['f7', 'f9', 'g7', 'g9'],
        'variant': ['q']
    },

    # STM32WB devices
    {
        'family': ['wb'],
        'name': ['30', '50']
    },

    # STM32WL devices
    {
        'family': ['wl'],
        'name': ['33']
    },{
        'family': ['wl'],
        'name': ['54', '55']
    },
]
