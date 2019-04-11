#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generic file input/output."""

from .h5 import *
from .xlsx import *
from .csv import *

supported = ('.h5', '.hdf', '.hdf5', '.xlsx', '.csv')


def ls(iname, path=None):
    """List contents of file / file structure"""

    if iname is None:
        return

    # file extension
    frmt = '.' + iname.split('.')[-1]

    # save configuration to output file
    if frmt in {'.h5', '.hdf5', '.hdf'}:
        h5ls(iname, path=path)
    elif frmt == '.xlsx':
        xlsxls(iname, path=path)
    elif frmt == '.csv':
        csvls(iname, path=path)
    else:
        raise RuntimeError('unknown file format `{}`'.format(frmt))


def save(oname, data, mode='a', force=True, path=None):
    """Save data to file / file structure"""

    if oname is None:
        return

    # file extension
    frmt = '.' + oname.split('.')[-1]

    # save configuration to output file
    if frmt in {'.h5', '.hdf5', '.hdf'}:
        to_hdf(oname, data, mode=mode, force=force, path=path)
    elif frmt == '.xlsx':
        to_xlsx(oname, data, mode=mode, force=force, path=path)
    elif frmt == '.csv':
        to_csv(oname, data, mode=mode, force=force, path=path)
    else:
        raise RuntimeError('unknown file format `{}`'.format(frmt))


def load(iname, path=None):
    """Load data from file / file structure"""

    if iname is None:
        return

    # file extension
    frmt = '.' + iname.split('.')[-1]

    # save configuration to output file
    if frmt in {'.h5', '.hdf5', '.hdf'}:
        return from_hdf(iname, path=path)
    elif frmt == '.xlsx':
        return from_xlsx(iname, path=path)
    elif frmt == '.csv':
        return from_csv(iname, path=path)
    else:
        raise RuntimeError('unknown file format `{}`'.format(frmt))
