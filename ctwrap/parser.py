#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parser object."""

from pint import UnitRegistry

ureg = UnitRegistry()

__all__ = ['Parser']


class Parser(object):
    """A lightweight class that handles units.

    The handling mimics that of a python dictionary, while adding direct access to 
    keyed values via attributes.
    """

    def __init__(self, dct):

        self._dict = dct

    def __getattr__(self, attr):

        if attr not in self._dict:
            raise AttributeError("unknown attribute '{}'".format(attr))

        return self[attr]

    def __getitem__(self, key):

        val = self._dict[key]

        if isinstance(val, (str, bool, int, float)):
            return val
        elif isinstance(val, list) and len(val) > 0:
            return ureg.Quantity(val[0], ureg[val[1]])

    def __repr__(self):
        return repr(self._dict)

    def keys(self):
        return self._dict.keys()
