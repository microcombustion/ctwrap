# -*- coding: utf-8 -*-
"""Helper functions"""

import re
import os
import yaml
import warnings
import pkg_resources

from copy import deepcopy
from pandas import read_excel

from pint import UnitRegistry, UndefinedUnitError
ureg = UnitRegistry()

# package data path
__DATA_PATH = pkg_resources.resource_filename('zerod', 'data')


def data_path():
    return __DATA_PATH


def load_xlsx(fname, path=None):

    if path is 'default':
        fname = (os.sep).join([__DATA_PATH, fname])
    else:
        fname = (os.sep).join([path, fname])

    return read_excel(fname, encoding="ISO-8859-1")


def load_yaml(fname, path=None, keys=None):

    if path is 'default':
        fname = (os.sep).join([__DATA_PATH, fname])
    else:
        fname = (os.sep).join([path, fname])

    with open(fname) as yml:
        out = parse_yaml(yml)

    if keys is None:
        return out
    else:
        return tuple([deepcopy(out[k]) for k in keys])


def parse_yaml(yml):
    """Load yaml

    Workaround for YAML bug, see:
    https://stackoverflow.com/questions/30458977/yaml-loads-5e-6-as-string-and-not-a-number
    """

    loader = yaml.SafeLoader
    loader.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(
            u'''^(?:[-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
            |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
            |\\.[0-9_]+(?:[eE][-+][0-9]+)?
            |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
            |[-+]?\\.(?:inf|Inf|INF)
            |\\.(?:nan|NaN|NAN))$''', re.X), list(u'-+0123456789.'))

    return yaml.load(yml, Loader=loader)


def get_values(dic):
    """Get values from dictionary"""

    out = {}
    err = 'undefined unit for `{}`: `{}`'
    for key in dic:
        val = dic[key]
        if isinstance(val, list) and len(val) > 1:
            if val[1] not in {'polynomial'}:
                a = ureg.parse_expression(val[1])
            out[key] = val[0]
        elif isinstance(val, (str, object)):
            out[key] = val
        else:
            print(val)
            print(type(val))
            raise ValueError('missing unit specification')
    return out


def to_yaml(val):
    """save to yaml string"""

    # dump into yaml string and clean up result
    # (pre-emptive due to 'bugs' in yaml package)
    info = yaml.dump(val)
    info = info.replace("'''", "|").replace("'", "").replace("|", "'")
    info = info.replace('(', '!!python/tuple [').replace(')', ']')
    info = info.strip().rstrip('.').strip()
    return info


def from_yaml(val):
    """recover from (yaml) string"""

    # recover content of string
    return yaml.load(val)


def flatten(d):
    """Flatten nested dictionary"""

    out = {}
    for k, v in d.items():
        if isinstance(v, dict):

            # recursion
            inner = flatten(v)
            out.update({'{}.{}'.format(k, kk): vv for kk, vv in inner.items()})

        else:

            # ensure saved data is in string format
            if isinstance(v, tuple):
                out[k] = to_yaml(v)
            elif isinstance(v, list):
                out[k] = to_yaml(v)
            elif v is None:
                out[k] = 'None'
            else:
                out[k] = to_yaml(v)

    return out


def nested(d):
    """Create nested dictionary"""

    out = {}
    keys = list(d.keys())
    ukeys = list(set([k.split('.')[0] for k in keys]))
    ukeys.sort()

    for uk in ukeys:

        if uk in keys:

            # recreate tuple / string
            if isinstance(d[uk], str):
                out[uk] = from_yaml(d[uk])
                if out[uk] == 'None':
                    out[uk] = None
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
