# -*- coding: utf-8 -*-
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

avr_groups = \
[
    # AT90 devices
    {
        'family': ['90'],
        'name': ['1', '2', '216'],
        'type': ['pwm']
    },{
        'family': ['90'],
        'name': ['3', '316'],
        'type': ['pwm']
    },{
        'family': ['90'],
        'name': ['32', '64', '128'],
        'type': ['can']
    },{
        'family': ['90'],
        'name': ['82', '162'],
        'type': ['usb']
    },{
        'family': ['90'],
        'name': ['81', '161'],
        'type': ['pwm']
    },{
        'family': ['90'],
        'name': ['646', '647', '1286', '1287'],
        'type': ['usb']
    },

    # ATtiny devices
    {
        'family': ['tiny'],
        'name': ['4', '5', '9', '10'],
    },{
        'family': ['tiny'],
        'name': ['11', '12', '13', '15'],
    },{
        'family': ['tiny'],
        'name': ['20'],
    },{
        'family': ['tiny'],
        'name': ['24', '44', '84'],
    },{
        'family': ['tiny'],
        'name': ['25', '45', '85'],
    },{
        'family': ['tiny'],
        'name': ['26'],
    },{
        'family': ['tiny'],
        'name': ['40'],
    },{
        'family': ['tiny'],
        'name': ['43'],
    },{
        'family': ['tiny'],
        'name': ['48', '88'],
    },{
        'family': ['tiny'],
        'name': ['80', '840'],
    },{
        'family': ['tiny'],
        'name': ['87', '167'],
    },{
        'family': ['tiny'],
        'name': ['102', '104'],
    },{
        'family': ['tiny'],
        'name': ['202', '402', '802'],
    },{
        'family': ['tiny'],
        'name': ['204', '404', '406', '804', '806', '807', '1604', '1606', '1607'],
    },{
        'family': ['tiny'],
        'name': ['212', '412'],
    },{
        'family': ['tiny'],
        'name': ['261', '461', '861'],
    },{
        'family': ['tiny'],
        'name': ['441', '841'],
    },{
        'family': ['tiny'],
        'name': ['416', '816', '1616', '3216'],
    },{
        'family': ['tiny'],
        'name': ['417', '817', '1617', '3217'],
    },{
        'family': ['tiny'],
        'name': ['214', '414', '814', '1614', '3214'],
    },{
        'family': ['tiny'],
        'name': ['828'],
    },{
        'family': ['tiny'],
        'name': ['1634'],
    },{
        'family': ['tiny'],
        'name': ['2313', '4313'],
    },

    # ATmega devices
    {
        'family': ['mega'],
        'name': ['8', '16', '32'],
        'type': ['u2']
    },{
        'family': ['mega'],
        'name': ['8', '16', '32'],
        'type': ['', 'a', 'l']
    },{
        'family': ['mega'],
        'name': ['8', '16'],
        'type': ['hva']
    },{
        'family': ['mega'],
        'name': ['16', '32'],
        'type': ['u4', 'u4rc']
    },{
        'family': ['mega'],
        'name': ['16', '32'],
        'type': ['hvb', 'hvbrevb']
    },{
        'family': ['mega'],
        'name': ['16', '32', '64'],
        'type': ['hve2']
    },{
        'family': ['mega'],
        'name': ['48', '88', '168', '328'],
        'type': ['', 'a', 'p', 'pa', 'v', 'pv']
    },{
        'family': ['mega'],
        'name': ['48', '88', '168', '328'],
        'type': ['pb']
    },{
        'family': ['mega'],
        'name': ['64', '128'],
        'type': ['', 'a', 'l']
    },{
        'family': ['mega'],
        'name': ['64', '128', '256'],
        'type': ['rfa1', 'rfr2']
    },{
        'family': ['mega'],
        'name': ['16', '32', '64', '128', '256'],
        'type': ['m1', 'c1']
    },{
        'family': ['mega'],
        'name': ['162'],
    },{
        'family': ['mega'],
        'name': ['164', '324', '644'],
        'type': ['', 'a', 'p', 'v', 'pa', 'pv']
    },{
        'family': ['mega'],
        'name': ['1284'],
        'type': ['', 'a', 'p', 'pa']
    },{
        'family': ['mega'],
        'name': ['164', '324', '644', '1284'],
        'type': ['pb']
    },{
        'family': ['mega'],
        'name': ['165', '325', '645'],
    },{
        'family': ['mega'],
        'name': ['169', '329', '649'],
    },{
        'family': ['mega'],
        'name': ['406'],
    },{
        'family': ['mega'],
        'name': ['640', '1280', '2560'],
    },{
        'family': ['mega'],
        'name': ['1281', '2561'],
    },{
        'family': ['mega'],
        'name': ['644', '1284', '2564'],
        'type': ['rfr2']
    },{
        'family': ['mega'],
        'name': ['3208', '3209', '4808', '4809'],
    },{
        'family': ['mega'],
        'name': ['3250', '6450'],
    },{
        'family': ['mega'],
        'name': ['3290', '6490'],
    },{
        'family': ['mega'],
        'name': ['8515'],
    },{
        'family': ['mega'],
        'name': ['8535'],
    },

    # xmega devices
    {
        'family': ['xmega'],
        'type': ['a1'],
    },{
        'family': ['xmega'],
        'type': ['a3'],
        'pin': ['', 'b']
    },{
        'family': ['xmega'],
        'type': ['a3'],
        'pin': ['bu', 'u']
    },{
        'family': ['xmega'],
        'type': ['a4'],
    },{
        'family': ['xmega'],
        'type': ['b1'],
    },{
        'family': ['xmega'],
        'type': ['b3'],
    },{
        'family': ['xmega'],
        'type': ['c3'],
    },{
        'family': ['xmega'],
        'type': ['c4'],
    },{
        'family': ['xmega'],
        'type': ['d3'],
    },{
        'family': ['xmega'],
        'type': ['d4'],
    },{
        'family': ['xmega'],
        'type': ['e5'],
    },
]
