# -*- coding: utf-8 -*-
# Copyright (c) 2018, Niklas Hauser
# All rights reserved.

import re
import logging
import CppHeaderParser

LOGGER = logging.getLogger('dfg.input.cmsis.header')

class CmsisHeader:
    """
    Reading one CMSIS header without expanding any source code though
    """

    REPLACE = [
        ("__IO", ""),
        ("__I", ""),
        ("__O", ""),
    ]

    @staticmethod
    def get_header(filename, replace = []):
        replacers = replace + CmsisHeader.REPLACE
        try:
            content = filename.read_text(encoding="utf-8", errors="replace")
            for r in replacers:
                content = re.sub(r[0], r[1], content, flags=(re.DOTALL | re.MULTILINE))
            # print(content)
            return CppHeaderParser.CppHeader(content, "string")
        except CppHeaderParser.CppParseError as e:
            LOGGER.error("Unable to parse '{}': {}".format(filename, str(e)))
            return None