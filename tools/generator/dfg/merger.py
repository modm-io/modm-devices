# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# All rights reserved.

import logging

LOGGER = logging.getLogger('dfg.merger')

class DeviceMerger:
    @staticmethod
    def merge(merge_group, devices):
        mergeable = [[] for _ in range(len(merge_group))]
        result = []

        for device in devices:
            index = DeviceMerger._get_index_for_id(merge_group, device.ids[0])
            if index >= 0:
                mergeable[index].append(device)
            else:
                device._sortTree()
                result.append(device)
                LOGGER.warning("Unmergeable device '%s'", device.ids[0].string)

        for group in [g for g in mergeable if len(g)]:
            device = group[0]
            for d in group[1:]:
                device.merge(d)
            device._sortTree()
            result.append(device)

        return result

    @staticmethod
    def _get_index_for_id(merge_group, did):
        for group in merge_group:
            if all(did[key] in value for key, value in group.items()):
                return merge_group.index(group)

        return -1
