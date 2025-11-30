#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pkgutil helper package.

Adds a function that returns the filename rather than the content in a similar
fashion to pkgutil.get_data().
"""

import os
import re

import urllib.request
import urllib.parse

def naturalkey(key):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    def atoi(text):
        try:
            return int(text)
        except ValueError:
            return text

    return [atoi(c) for c in re.split(r"([-]?\d+)", key)]


def get_filename(package, resource):
    """Rewrite of pkgutil.get_data() that return the file path.
    """
    if os.sys.version_info >= (3, 14):
        import importlib.resources
        package_files = importlib.resources.files(package)
        return (package_files / resource).resolve()

    # Old deprecated way to work with Python ≤3.8
    import sys
    import pkgutil

    loader = pkgutil.get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None

    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    return os.path.normpath(os.path.join(*parts))


CATALOGFILE = get_filename('modm_devices', 'resources/catalog.xml')
os.environ['XML_CATALOG_FILES'] = \
    urllib.parse.urljoin('file:', urllib.request.pathname2url(CATALOGFILE))
