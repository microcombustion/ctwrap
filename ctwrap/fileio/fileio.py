#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generic file input/output."""

from .h5 import *
from .xlsx import *
from .csv import *

supported = ('.h5', '.hdf', '.hdf5', '.xlsx', '.csv')


def save(oname, data, mode='a', force=True, path=None):

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
