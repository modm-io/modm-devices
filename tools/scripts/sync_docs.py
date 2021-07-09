#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, os, sys
from pathlib import Path
from jinja2 import Environment
from collections import defaultdict

rootpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")
sys.path.append(rootpath)
import modm_devices.parser

TABLE_TEMPLATE = """
| Family        | Devices | Family        | Devices | Family        | Devices |
|:--------------|:--------|:--------------|:--------|:--------------|:--------|
{% for (family, count) in families.items() | sort %}| {{ "%-14s" | format(family) }}|  {{ "%4s" | format(count) }}   {% if loop.index % 3 == 0 or loop.last %}|
{% endif %}{% endfor %}
"""

def format_table(families):
    subs = {"families": families}
    return Environment().from_string(TABLE_TEMPLATE).render(subs)

def replace(text, key, content):
    return re.sub(r"<!--{0}-->.*?<!--/{0}-->".format(key), "<!--{0}-->{1}<!--/{0}-->".format(key, content), text, flags=re.DOTALL | re.MULTILINE)

def extract(text, key):
    return re.search(r"<!--{0}-->(.*?)<!--/{0}-->".format(key), text, flags=re.DOTALL | re.MULTILINE).group(1)

if __name__ == "__main__":
    devices_short = set()
    devices = []
    for filename in Path(rootpath).glob("devices/**/*.xml"):
        for d in modm_devices.parser.DeviceParser().parse(str(filename)).get_devices():
            short_device = d.identifier.string.split("@")[0]
            if short_device not in devices_short:
                devices_short.add(short_device)
                devices.append(d)

    families = defaultdict(int)
    for dev in devices:
        did = dev.identifier
        family = did.string.split(did.family)[0] + did.family
        families[family.upper()] += 1

    readme_path = Path(rootpath) / "README.md"
    readme = readme_path.read_text()
    readme = replace(readme, "devicetable", format_table(families))
    readme = replace(readme, "devicecount", sum(families.values()))
    readme_path.write_text(readme)



