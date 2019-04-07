#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Object handling configurations."""

import os
from pandas import ExcelWriter

__all__ = ['Configuration']


class Configuration(object):
    """Configuration handler.

    Class handles configurations (typically based on dictionary of dictionaries
    loaded from YAML file). 

    Attributes are handled dynamically, where keys of constructor keyword arguments
    are mapped to attributes.
    """

    def __init__(self, verbosity=None, **kwargs):
        """Constructor of configuration handling class.

        Kwargs:
           verbosity (int): verbosity level (ignored)
           plus keywords to be mapped to attributes.
        """

        # parse arguments
        self._config = kwargs.copy()

        # ensure all settings are set
        err = '`{}` not specified'
        for k in self._config.keys():
            assert self._config[k] is not None, err.format(k)

    @property
    def attributes(self):
        """attributes"""
        return list(self._config.keys())

    def __call__(self):
        return self._config

    def __getattr__(self, attr):
        """Access settings dictionary as attribute"""

        assert attr in self._config.keys(), 'invalid attribute'
        return self._config[attr]
