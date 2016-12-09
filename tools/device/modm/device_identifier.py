#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import re
import logging
import copy
import itertools
import string
from collections import OrderedDict
from collections import defaultdict

class DeviceIdentifier:
    """ DeviceIdentifier
    """

    def __init__(self):
        self.properties = OrderedDict()
        self.naming_schema = None
        self.__string = None

    def copy(self):
        identifier = DeviceIdentifier()
        identifier.properties = copy.deepcopy(self.properties)
        identifier.naming_schema = self.naming_schema
        return identifier

    @property
    def string(self):
        # if no naming schema is available, throw up
        if self.naming_schema is None:
            raise DeviceIdentifierException("Naming schema is missing!")
        # Use the naming schema to generate the string
        if self.__string is None:
            self.__string = string.Formatter().vformat(
                    self.naming_schema, (), defaultdict(str, **self.properties))
        return self.__string

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __getitem__(self, key):
        if key in self.properties:
            return self.properties[key]
        return None

    def __eq__(self, other):
        return self.string == other.string

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(str(self.properties))

    def __str__(self):
        return self.string


class MultiDeviceIdentifier:
    """ MultiDeviceIdentifier
    Encapsulates a list of DeviceIdentifier.
    This manages filtering, merging and accessing.
    """
    def __init__(self, device_id=None):
        self.ids = []
        if isinstance(device_id, DeviceIdentifier):
            self.ids = [device_id.copy()]

    def copy(self):
        return MultiDeviceIdentifier.from_list(self.ids)

    @staticmethod
    def from_list(device_ids: list):
        mid = MultiDeviceIdentifier()
        mid.ids = [dev.copy() for dev in device_ids]
        return mid

    def append(self, device_id):
        assert isinstance(device_id, DeviceIdentifier)
        assert all(device_id.naming_schema == d.naming_schema for d in self.ids)

        self.ids.append(device_id)
        self.ids = list(set(self.ids))
        self.ids.sort(key=lambda k : k.string)

    def extend(self, identifier):
        assert isinstance(identifier, MultiDeviceIdentifier)
        assert all(all(i.naming_schema == d.naming_schema for d in self.ids) for i in identifier)

        self.ids.extend(identifier)
        self.ids = list(set(self.ids))
        self.ids.sort(key=lambda k : k.string)

    @property
    def string(self):
        # Format the property dictionaries as a string
        ident = DeviceIdentifier()
        ident.naming_schema = self.naming_schema
        for k in self.keys():
            v = self.getAttribute(k)
            if len(v) > 0:
                fmt = "[{}]" if len(v) > 1 else "{}"
                ident[k] = fmt.format("|".join(v))
        return ident.string

    def subtract(self, others):
        assert isinstance(others, MultiDeviceIdentifier)
        ids = MultiDeviceIdentifier()

        for k in self.keys():
            me = self.getAttribute(k)
            other = others.getAttribute(k)
            if me != other:
                for m in me:
                    ident = DeviceIdentifier()
                    ident.naming_schema = self.naming_schema
                    ident[k] = m
                    ids.append(ident)
        return ids

    def product(self):
        return MultiDeviceIdentifier.from_product(self, self.naming_schema)

    @staticmethod
    def from_product(properties, naming_schema):
        attributes = list(itertools.product(*properties.values()))
        ids = MultiDeviceIdentifier()
        for attr in attributes:
            ident = DeviceIdentifier()
            ident.naming_schema = naming_schema
            for ii, k in enumerate(properties.keys()):
                ident[k] = attr[ii]
            ids.append(ident)
        return ids

    def minimal_subtract(self, complete, others):
        assert isinstance(complete, MultiDeviceIdentifier)

        def minimal_keys(absolute, diff):
            keys = diff.keys()
            for clength in range(len(keys)):
                for kcomb in itertools.combinations(keys, clength):
                    filtered = complete.filter(lambda i: any(i[k] in diff.getAttribute(k) for k in kcomb))
                    if filtered == absolute:
                        return kcomb
            return keys

        diff = self.subtract(others)

        ids = MultiDeviceIdentifier()
        for k in minimal_keys(self, diff):
            for m in diff.getAttribute(k):
                ident = DeviceIdentifier()
                ident.naming_schema = self.naming_schema
                ident[k] = m
                ids.append(ident)

        return ids

    def minimal_invertible_subtract(self, complete, others):
        if (len(self.ids) * 2 > len(complete.ids)):
            # invert it
            ids_inv = complete.copy()
            ids_inv.ids = [did for did in ids_inv.ids if did not in self.ids]
            return (ids_inv.minimal_subtract(complete, others), -1)
        else:
            return (self.minimal_subtract(complete, others), 1)

    def filter(self, filter_fn):
        ids = MultiDeviceIdentifier()

        for did in self.ids:
            if filter_fn(did):
                ids.append(did)

        return ids

    def keys(self):
        keys = []
        for ident in self.ids:
            for k in ident.properties.keys():
                if k not in keys:
                    keys.append(k)
        return keys

    def items(self):
        items = {}
        for k in self.keys():
            items[k] = self.getAttribute(k)
        return items.items()

    def values(self):
        values = []
        for k in self.keys():
            values.append(self.getAttribute(k))
        return values

    @property
    def naming_schema(self):
        if len(self.ids):
            return self.ids[0].naming_schema
        return ""

    def remove(self, device_id):
        self.ids.remove(device_id)

    def __contains__(self, other):
        if isinstance(other, DeviceIdentifier):
            return any(other == dev for dev in self.ids)
        if isinstance(other, MultiDeviceIdentifier):
            return all(did in self for did in other)
        return NotImplemented

    def __eq__(self, others):
        return set(others.ids) == set(self.ids)

    def __iter__(self):
        for device_id in self.ids:
            yield device_id

    def __getitem__(self, index):
        return self.ids[index]

    def __len__(self):
        return len(self.ids)

    def __hash__(self):
        return sum(hash(did) for did in self.ids)

    def getAttribute(self, name):
        if '@' in name:
            attr = [getattr(i, name[1:]) for i in self.ids]
        else:
            attr = [i[name] for i in self.ids]

        attr = [a for a in attr if a is not None]
        attr = list(set(attr))
        try:
            attr.sort(key=int)
        except:
            attr.sort()
        return attr

    def __str__(self):
        return self.string
