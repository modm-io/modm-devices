# -*- coding: utf-8 -*-
# Copyright (c) 2016, Fabian Greif
# Copyright (c) 2016, Niklas Hauser
# All rights reserved.

import logging.config

def configure_logger(level):
    """
    Load the default configuration for the logger.
    """
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'full': {
                # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                'format': '[%(levelname)s] %(name)s: %(message)s'
            },
            'simple': {
                'format': '%(message)s'
            },
        },
        'handlers': {
            'default': {
                'class':'logging.StreamHandler',
                'formatter': 'full',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': level,
                'propagate': True
            }
        }
    })
