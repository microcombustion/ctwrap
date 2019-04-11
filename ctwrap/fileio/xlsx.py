#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functions handling Excel input/output"""

import pandas as pd
import os

# filter warning as group names may not be valid python identifiers
import warnings
warnings.filterwarnings("ignore",
                        "object name is not a valid Python identifier:")

# local imports
from .yaml import flatten, nested

__all__ = ['xlsxls', 'to_xlsx', 'from_xlsx']


def _getfile(fname, path=None):
    """helper function"""

    if path not in ['', None]:
        fname = (os.sep).join([path, fname])

    return fname, os.path.isfile(fname)


def xlsxls(iname, path=None):
    """Retrieve names of sheets within a xlsx file"""

    fname, fexists = _getfile(iname, path=path)
    if not fexists:
        return []

    with pd.ExcelFile(fname) as xlsx:
        sheets = [s for s in reac.sheet_names]

    return sheets


def to_xlsx(oname, sheets, path=None, mode='a', force=True):
    """Write content to sheet(s) of xlsx file"""

    # file check
    fname, fexists = _getfile(oname, path=path)
    if fexists and mode == 'w' and not force:
        msg = 'Cannot overwrite existing file `{}` (use force to override)'
        raise RuntimeError(msg.format(oname))

    existing = xlsxls(fname)
    for s in sheets:

        if mode == 'a' and s in existing and not force:
            msg = 'Cannot overwrite existing sheet `{}` (use force to override)'
            raise RuntimeError(msg.format(key))

        data = sheets[s]
        if isinstance(data, dict):
            data = pd.Series(flatten(data))
            with pd.ExcelWriter(fname, engine='openpyxl', mode=mode) as writer:
                data.to_excel(writer, sheet_name=s)
        elif isinstance(data, (pd.DataFrame, pd.Series)):
            with pd.ExcelWriter(fname, engine='openpyxl', mode=mode) as writer:
                data.to_excel(writer, sheet_name=s)
        elif data is None:
            # print('no data frame')
            pass
        else:
            # ignore anything else
            pass

        # prevent overwriting of existing sheets
        mode = 'a'


def from_xlsx(iname, path=None):
    """Load content from xlsx file"""

    # check file
    iname, fexists = _getfile(iname, path=path)
    if not fexists:
        msg = 'File `{}` does not exist'
        raise RuntimeError(msg.format(oname))

    # retrieve content
    with pd.ExcelFile(iname) as xlsx:

        sheets = xlsx.sheet_names

        out = {}
        for s in sheets:

            data = pd.read_excel(xlsx, s)
            if isinstance(data, pd.Series):
                data = nested(dict(data))
            out[s] = data

    return out
