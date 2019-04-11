#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Excel file input/output"""

import pandas as pd
import os

# local imports
from .yaml import flatten, nested

__all__ = ['csvls', 'to_csv', 'from_csv']


def csvls(iname, path=None):

    raise NotImplementedError('to be done')


def to_csv(oname, groups, path=None, mode='a', force=True):

    raise NotImplementedError('to be done')


def from_csv(iname, path=None):

    raise NotImplementedError('to be done')
