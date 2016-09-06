#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Device:
    def __init__(self):
        self.platform = None
        self.family = None
        self.name = None
        self.type = None
        self.pin_id = None
        self.size_id = None
        
        self.partname = ""
    
    def __str__(self):
        return self.partname

class Selector:
    def __init__(self):
        self.property = {
            "platform": [],
            "family": [],
            "name": [],
            "type": [],
            "pin_id": [],
            "size_id": []
        }
    
    def match(self, device):
        for key, values in self.property.items():
            if values is None or len(values) == 0:
                continue
            
            if getattr(device, key) not in values:
                return False
        return True
