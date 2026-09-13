# Copyright 2013, Niklas Hauser
# Copyright 2016, Fabian Greif
# SPDX-License-Identifier: MPL-2.0

import logging

LOGGER = logging.getLogger(__name__)


def group_index(groups: list[dict[str, list[str]]], did) -> int:
    """
    :param groups: A list of merge groups, each a mapping of identifier key to allowed values.
    :param did: A device identifier.
    :return: The index of the first merge group matching the identifier or -1.
    """
    for index, group in enumerate(groups):
        if all(did[key] in value for key, value in group.items()):
            return index
    return -1


def merge(groups: list[dict[str, list[str]]], devices) -> list:
    """
    Merges all device trees belonging to the same merge group into one tree.
    Devices that do not match any group are left unmerged.

    :param groups: A list of merge groups, each a mapping of identifier key to allowed values.
    :param devices: The device trees to merge.
    :return: A list of merged device trees.
    """
    mergeable = [[] for _ in range(len(groups))]
    result = []

    for device in devices:
        index = group_index(groups, device.ids[0])
        if index >= 0:
            mergeable[index].append(device)
        else:
            device._sortTree()
            result.append(device)
            LOGGER.info("Unmergeable device '%s'", device.ids[0].string)

    for group in [g for g in mergeable if len(g)]:
        device = group[0]
        for d in group[1:]:
            device.merge(d)
        device._sortTree()
        result.append(device)

    return result


def filename_from_ids(
    ids, fmt: str, empty: str = None, sort_keys: tuple[str] = ()
) -> str:
    """
    Formats a device file name from the identifier values joined by underscores.

    :param ids: The merged device identifiers.
    :param fmt: The format string using the identifier keys.
    :param empty: Replace empty values with this string.
    :param sort_keys: Sort the values of these keys alphabetically.
    :return: The formatted file name.
    """
    p = {}
    for k in ids.keys():
        v = [
            (empty if (empty is not None and b == "") else b)
            for b in ids.getAttribute(k)
        ]
        if k in sort_keys:
            v.sort()
        if len(v) > 0:
            p[k] = "_".join(v)
    return fmt.format(**p)
