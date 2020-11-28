#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Function handling file input/output."""

import os
import re

try:
    import ruamel_yaml as yaml
except ImportError:
    from ruamel import yaml

from copy import deepcopy

__all__ = ['load_yaml', 'flatten', 'nested']


def load_yaml(fname, path=None, keys=None):
    """Load yaml from file

    Arguments:
        fname (str): file name

    Keyword Arguments:
        path (str): relative/absolute path. Empty ('') for
    """

    if path is 'default':
        fname = (os.sep).join([__DATA_PATH, fname])
    elif path not in ['', None]:
        fname = (os.sep).join([path, fname])

    with open(fname) as yml:
        out = yaml.load(yml, Loader=yaml.SafeLoader)

    if keys is None:
        return out
    else:
        return tuple([deepcopy(out[k]) for k in keys])


def flatten(d):
    """Flatten nested dictionary (recursive function)"""

    out = {}
    for k, v in d.items():
        if isinstance(v, dict):

            # recursion
            inner = flatten(v)
            out.update({'{}.{}'.format(k, kk): vv for kk, vv in inner.items()})

        else:

            # ensure all saved data is in string format
            if isinstance(v, (tuple, list)):
                out[k] = yaml.dump(v).rstrip()
            elif v is None:
                out[k] = 'null'
            else:
                # note: yaml.dump() adds '\n...\n' to scalars
                out[k] = yaml.dump(v).rstrip().rstrip('.').rstrip()

    return out


def nested(d):
    """Create nested dictionary (recursive function)"""

    out = {}
    keys = list(d.keys())
    ukeys = list(set([k.split('.')[0] for k in keys]))
    ukeys.sort()

    loader = yaml.SafeLoader
    for uk in ukeys:

        if uk in keys:

            # recreate tuple / string
            if isinstance(d[uk], str):
                out[uk] = yaml.load(d[uk], Loader=loader)
            else:
                out[uk] = d[uk]

        else:

            # start recursion
            replace = '{}.'.format(uk)
            inner = {
                kk.replace(replace, ''): vv
                for kk, vv in d.items() if uk in kk
            }
            out[uk] = nested(inner)

    return out
