# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import logging

from enum import Enum
from collections import OrderedDict

from modm.device_identifier import MultiDeviceIdentifier

LOGGER = logging.getLogger('dfg.tree')

class DeviceTree:
    """ DeviceTree
    Abstracts a generic tree, loosely based on XML.
    """

    def __init__(self, name=None):
        self.parent = None
        self.children = []

        self.ids = MultiDeviceIdentifier()

        self.name = str(name)
        self.attributes = OrderedDict()

        self.sortKeys = []
        self.identKey = self._toCompactString()

    def setAttributes(self, *args):
        if isinstance(args[0], list) and isinstance(args[1], dict):
            for k in args[0]:
                if k in args[1]:
                    self.setAttribute(k, args[1][k])
            return
        if isinstance(args[0], dict):
            LOGGER.error("Unordered dictionaries are not accepted!")
            return

        assert len(args) % 2 == 0
        for ii in range(len(args) // 2):
            self.setAttribute(args[ii * 2], args[ii * 2 + 1])

    def setAttribute(self, key, value):
        if key in self.attributes:
            LOGGER.warning("Overwriting attribute '%s'", key)
        self.attributes[key] = str(value)

    def removeAttribute(self, key):
        if key in self.attributes:
            del self.attributes[key]

    def addChild(self, name):
        element = DeviceTree(name)
        element.parent = self
        element.ids = self.ids.copy()
        self.children.append(element)
        return element

    def prependChild(self, name):
        element = DeviceTree(name)
        element.parent = self
        element.ids = self.ids.copy()
        self.children.insert(0, element)
        return element

    def setValue(self, value):
        self.setAttribute('value', str(value))

    def addSortKey(self, key):
        self.sortKeys.append(key)

    def setIdentifier(self, key):
        self.identifier = key

    def _identifier(self):
        return self.identifier(self)

    def __getitem__(self, item):
        if item in self.attributes:
            return self.attributes[item]
        return None

    def _sortTree(self):
        for key in self.sortKeys:
            self.children.sort(key=key)
        for ch in self.children:
            ch._sortTree()

    def toString(self, indent=0):
        ind = ' ' * indent
        if indent >= 2:
            ind = ind[:-2] + '. '
        ident = self.ids.string
        if self.parent is not None and self.parent.ids.string == ident:
            ident = ""
        string = "{}{} {}\n".format(
            ind,
            self._toCompactString(),
            ident)
        for ch in self.children:
            string += ch.toString(indent + 2)
        return string

    def _toCompactString(self):
        string = "{} <{}>".format(
            self.name,
            " ".join(["{}:{}".format(k,v) for k,v in self.attributes.items()])
        )
        return string

    def merge(self, other):
        if self == other:
            self.ids.extend(other.ids)
            self._merge(other)

    def _merge(self, other):
        other_remaining = list(other.children)
        remaining = []
        merge_list = []

        for child in self.children:
            for other in other_remaining:
                if other == child:
                    other_remaining.remove(other)
                    merge_list.append( (child, other) )
                    break
            else:
                remaining.append(child)
        remaining.extend(other_remaining)

        merged_children = []
        for child, other in merge_list:
            child.ids.extend(other.ids)
            other.parent = self
            child._merge(other)
            merged_children.append(child)

        for rem in remaining:
            rem.parent = self
            merged_children.append(rem)

        self.children = merged_children

    def __eq__(self, other):
        return self._toCompactString() == other._toCompactString()

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self._toCompactString())

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self._toCompactString()
