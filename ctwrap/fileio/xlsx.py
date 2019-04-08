#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Excel file input/output"""

import pandas as pd
from .yaml import flatten, nested
###from ..configuration import Configuration

__all__ = ['xlsxls', 'to_xlsx', 'from_xlsx']


def xlsxls(fname):

    raise NotImplementedError('to be done')


def to_xlsx(fname):

    raise NotImplementedError('to be done')


def load_xlsx(fname, path=''):

    if path is 'default':
        fname = (os.sep).join([__DATA_PATH, fname])
    elif path is not '':
        fname = (os.sep).join([path, fname])

    return pd.read_excel(fname, encoding="ISO-8859-1")


# meta = pd.Series(flatten(self._configuration))
# with pd.ExcelWriter(
#         fname, engine='openpyxl', mode='w') as writer:
#     meta.to_excel(writer, sheet_name='configuration')

# # # save information on variation (if available)
# if self._variation is not None:
#     with pd.ExcelWriter(
#             fname, engine='openpyxl', mode='a') as writer:
#         var.to_excel(writer, sheet_name='variation')

# # Excel
# with ExcelWriter(fname, engine='openpyxl', mode='a') as writer:
#     df[keys].to_excel(writer, sheet_name=key)


def from_xlsx(fname):
    """load content from xlsx file"""

    reac = pd.ExcelFile(fname)
    sheets = [
        s for s in reac.sheet_names if s not in ['configuration', 'variation']
    ]
    sheets.sort(key=lambda f: int(''.join(list(filter(str.isdigit, f)))))
    data = {s: pd.read_excel(reac, s) for s in sheets}

    if 'configuration' in reac.sheet_names:
        df = pd.read_excel(reac, 'configuration')
        keys = df.keys()
        config = dict(zip(df[keys[0]], df[keys[1]]))
        config = nested(config)
        #config = Configuration(**config)
    else:
        config = None

    if 'variation' in reac.sheet_names:
        df = pd.read_excel(reac, 'variation')
        keys = df.keys()
        var = dict(zip(df[keys[0]], df[keys[1]]))
        var = nested(var)
    else:
        var = None

    return data, config, var
