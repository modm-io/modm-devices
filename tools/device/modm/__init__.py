#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Platform Generator
"""

from . import pkg
from . import exception
from . import device_file
from . import device_identifier
from . import device
from . import parser

from .pkg import naturalkey
from .exception import ParserException

__all__ = ['exception', 'device_file', 'device_identifier', 'device', 'parser', 'pkg']

__author__ = "Fabian Greif"
__copyright__ = "Fabian Greif"
__credits__ = ["Fabian Greif"]
__license__ = "Mozilla Public License 2.0"
__version__ = "0.1.0"
__maintainer__ = "Fabian Greif"
__email__ = "fabian.greif@rwth-aachen.de"
__status__ = "Pre-Alpha"
