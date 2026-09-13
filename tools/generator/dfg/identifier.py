# Copyright 2016, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

import itertools

from modm_data.kg import DeviceIdentifier


class MultiDeviceIdentifier:
    """
    Encapsulates a list of `DeviceIdentifier` and manages filtering, merging,
    and computing the minimal set of identifier attributes that describe a
    subset of devices.
    """

    def __init__(self, objs=None):
        self._ids = []
        self.__string = None
        self.__naming_schema = None
        self.__dirty = True

        if isinstance(objs, DeviceIdentifier):
            self._ids = [objs.copy()]
        if isinstance(objs, MultiDeviceIdentifier):
            self._ids = [dev for dev in objs.ids]

    @property
    def ids(self):
        if self.__dirty:
            self._ids = sorted(list(set(self._ids)), key=lambda d: d._ustring)
            self.__dirty = False
        return self._ids

    def copy(self):
        ids = MultiDeviceIdentifier.from_list(self.ids)
        ids.__string = self.__string
        ids.__naming_schema = self.__naming_schema
        return ids

    @staticmethod
    def from_list(device_ids: list):
        mid = MultiDeviceIdentifier()
        mid._ids = [dev for dev in device_ids]
        return mid

    def append(self, did):
        assert isinstance(did, DeviceIdentifier)
        self._ids.append(did)
        self.__dirty = True
        self.__string = None
        self.__naming_schema = None

    def extend(self, dids):
        assert isinstance(dids, (MultiDeviceIdentifier, list))
        self._ids.extend(dids)
        self.__dirty = True
        self.__string = None
        self.__naming_schema = None

    @property
    def string(self):
        if self.__string is None:
            # Format the property dictionaries as a string
            ident = DeviceIdentifier(self.naming_schema)
            for k in self.keys():
                v = self.getAttribute(k)
                if len(v) > 0:
                    fmt = "[{}]" if len(v) > 1 else "{}"
                    ident.set(k, fmt.format("|".join(v)))
            self.__string = ident.string
        return self.__string

    def product(self):
        return MultiDeviceIdentifier.from_product(self, self.naming_schema)

    @staticmethod
    def from_product(properties, naming_schema):
        attributes = list(itertools.product(*properties.values()))
        ids = MultiDeviceIdentifier()
        for attr in attributes:
            ident = DeviceIdentifier(naming_schema)
            for ii, k in enumerate(properties.keys()):
                ident.set(k, attr[ii])
            ids.append(ident)
        return ids

    def minimal_subtract_set(self, complete, parent):
        """
        Computes the minimal list of identifier attribute sets that select
        exactly these devices out of the `complete` set of devices, given that
        they are already a subset of the `parent` devices.
        """
        assert isinstance(complete, MultiDeviceIdentifier)

        def partly_inside(mkeys, ids, did):
            return any(all(cid[k] == did[k] for k in mkeys) for cid in ids)

        def minimal_keys():
            keys = [
                k
                for k in self.keys()
                if not all(all(s[k] == p[k] for p in parent) for s in self)
            ]
            for clength in range(len(keys)):
                for kcomb in itertools.combinations(keys, clength):
                    if not clength:
                        filtered = parent
                    else:
                        filtered = complete.filter(
                            lambda i: partly_inside(kcomb, self, i)
                        )
                    if filtered == self:
                        return kcomb
            return keys

        def filtered_by_keys(mkeys, ids):
            nids = MultiDeviceIdentifier()
            for k in mkeys:
                for m in ids.getAttribute(k):
                    ident = DeviceIdentifier(self.naming_schema)
                    ident.set(k, m)
                    nids.append(ident)
            return nids

        def product_inside(mkeys, ids, did):
            nids = ids.copy()
            nids.append(did)
            pids = filtered_by_keys(mkeys, nids).product()
            return all(partly_inside(mkeys, self, i) for i in pids)

        mkeys = minimal_keys()

        cids = [MultiDeviceIdentifier()]
        for did in self:
            for ids in cids:
                if product_inside(mkeys, ids, did):
                    ids.append(did)
                    break
            else:
                cids.append(MultiDeviceIdentifier(did))

        fids = [filtered_by_keys(mkeys, ids) for ids in cids]
        fids.sort(key=lambda d: d.string)
        return fids

    def filter(self, filter_fn):
        ids = MultiDeviceIdentifier()
        for did in self.ids:
            if filter_fn(did):
                ids.append(did)
        return ids

    def keys(self):
        keys = []
        for ident in self.ids:
            for k in ident.keys():
                if k not in keys:
                    keys.append(k)
        return keys

    def items(self):
        return {k: self.getAttribute(k) for k in self.keys()}.items()

    def values(self):
        return [self.getAttribute(k) for k in self.keys()]

    @property
    def naming_schema(self):
        if self.__naming_schema is None:
            schema_set = sorted(set(did.naming_schema for did in self.ids))
            self.__naming_schema = "".join(schema_set)
        return self.__naming_schema

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
        if "@" in name:
            attr = [getattr(i, name[1:]) for i in self.ids]
        else:
            attr = [i[name] for i in self.ids]

        attr = [a for a in attr if a is not None]
        attr = list(set(attr))
        try:
            attr.sort(key=int)
        except ValueError:
            attr.sort()
        return attr

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"MultiDeviceId({self.string})"
