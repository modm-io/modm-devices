#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Fabian Greif
# All rights reserved.

from . import common

class AttributePart:
    def __init__(self, name):
        self.name = name
    
    def get(self, device_identifier, as_tuple=False):
        return getattr(device_identifier, self.name)
    
    def set(self, device, value):
        setattr(device, self.name, value)


class FixedPart:
    def __init__(self, name):
        self.name = name
    
    def get(self, device_identifier, as_tuple=False):
        if as_tuple:
            # Convert to tuple
            return (self.name, )
        else:
            return self.name
    
    def set(self, device, value):
        pass


class Schema:
    """
    Represents a naming schema.
    
    A naming schema consists of attribute and fixed parts. Attribute parts
    use one field of the device identifier to create the name part. Fixed parts
    a just a static string.
    """
    START_TOKEN = "{{"
    END_TOKEN = "}}"
    
    def __init__(self):
        self.parts = []
    
    def get_name(self, device_identifier):
        name = []
        for part in self.parts:
            name.append(part.get(device_identifier))
        return "".join(name)
    
    @staticmethod
    def parse(schema_string):
        schema = Schema()
        
        # Split by the starting token. Apart from the first entry every
        # following list entry is an attribute part. If the first entry is
        # not empty it is an fixed part.
        beginning = schema_string.split(Schema.START_TOKEN)
        if beginning[0] != '':
            schema.parts.append(FixedPart(beginning[0]))
        beginning = beginning[1:]
        
        for token in beginning:
            # All list entries are an attribute part and a following fixed
            # part (if the second entry is not empty).
            t = token.split(Schema.END_TOKEN)
            value = t[0].strip()
            if len(t) != 2:
                raise common.ParserException("Invalid format of name schema " \
                                             "string: '{}'".format(schema_string))
            schema.parts.append(AttributePart(value))
            if t[1] != '':
                schema.parts.append(FixedPart(t[1]))
        
        return schema
