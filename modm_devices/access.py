#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy

def copy_keys(src, *keys):
    dest = {};
    for key in keys:
        conv = lambda o: o
        if isinstance(key, tuple):
            key, conv = key
        if key in src:
            dest[key] = conv(src[key])
    return dest

def copy_deep(obj):
    return copy.deepcopy(obj)


class ReadOnlyList(list):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("You are trying to modify read-only DeviceFile data!")
    pop = __readonly__
    remove = __readonly__
    append = __readonly__
    clear = __readonly__
    extend = __readonly__
    insert = __readonly__
    reverse = __readonly__
    __copy__ = list.copy
    __deepcopy__ = copy._deepcopy_dispatch.get(list)
    del __readonly__


class ReadOnlyDict(dict):
    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("You are trying to modify read-only DeviceFile data!")
    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    __copy__ = dict.copy
    __deepcopy__ = copy._deepcopy_dispatch.get(dict)
    del __readonly__


def read_only(obj):
    if isinstance(obj, dict):
        return ReadOnlyDict(obj)
    if isinstance(obj, list):
        return ReadOnlyList(obj)
    return obj
