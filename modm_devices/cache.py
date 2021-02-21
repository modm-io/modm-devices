#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools

class cached_property(object):
    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value

cached_function = functools.lru_cache(None)
