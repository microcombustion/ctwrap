#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functions handling h5 (hdf5) input/output."""

import pandas as pd
import os

# filter warning as group names may not be valid python identifiers
import warnings
warnings.filterwarnings("ignore",
                        "object name is not a valid Python identifier:")

# local imports
from .yaml import flatten, nested

__all__ = ['h5ls', 'to_hdf', 'from_hdf']


def _getfile(fname, path=None):
    """helper function"""

    if path not in ['', None]:
        fname = (os.sep).join([path, fname])

    return fname, os.path.isfile(fname)


def h5ls(iname, path=None):
    """Retrieve names of groups within a hdf file."""

    fname, fexists = _getfile(iname, path=path)
    if not fexists:
        return []

    with pd.HDFStore(fname) as hdf:
        groups = [k.lstrip('/') for k in hdf.keys()]

    # equivalent with h5py
    # with h5py.File(fname, 'r') as hdf:
    #     groups = {k: 'Group' for k in hdf.keys()}

    return groups


def to_hdf(oname, groups, path=None, mode='a', force=True):
    """Write content to group(s) of hdf5 container """

    # file check
    fname, fexists = _getfile(oname, path=path)
    if fexists and mode == 'w' and not force:
        msg = 'Cannot overwrite existing file `{}` (use force to override)'
        raise RuntimeError(msg.format(oname))

    existing = h5ls(fname)
    for g in groups:

        if mode == 'a' and g in existing and not force:
            msg = 'Cannot overwrite existing group `{}` (use force to override)'
            raise RuntimeError(msg.format(key))

        data = groups[g]
        if isinstance(data, dict):
            data = pd.Series(flatten(data))
            data.to_hdf(fname, g, mode=mode)
        elif isinstance(data, (pd.DataFrame, pd.Series)):
            data.to_hdf(fname, g, mode=mode)
        elif data is None:
            # print('no data frame')
            pass
        else:
            # ignore anything else
            pass

        # prevent overwriting of existing groups
        mode = 'a'


def from_hdf(iname, path=None):
    """Load content from hdf file"""

    # check file
    fname, fexists = _getfile(iname, path=path)
    if not fexists:
        msg = 'File `{}` does not exist'
        raise RuntimeError(msg.format(oname))

    # retrieve content
    with pd.HDFStore(fname) as hdf:
        groups = [k.lstrip('/') for k in hdf.keys()]

        out = {}
        for g in groups:

            data = pd.read_hdf(hdf, g)
            if isinstance(data, pd.Series):
                data = nested(dict(data))
            out[g] = data

    return out
