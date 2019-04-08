#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Preprocessing functions."""

import cantera as ct
import os

from . import fileio

__all__ = ['parse_chemistry']

from pint import UnitRegistry, UndefinedUnitError

ureg = UnitRegistry()


def get_value(dct, key, unit=None, enforce=True):
    """Get value and convert units from dictionary entry"""

    assert key in dct, 'keyword `{}` not found'.format(key)

    val = dct[key]
    if isinstance(val, (str, bool, int)):
        return val
    elif isinstance(val, float):
        if enforce:
            raise RuntimeError('units for `{}` are enforced'.format(key))
        else:
            return val
    elif isinstance(val, list) and len(val) > 0:
        vv = ureg.Quantity(val[0], ureg[val[1]])
        if unit is not None:
            vv = vv.to(ureg[unit])
        return vv.magnitude
    else:
        raise NotImplementedError(
            'structure of `{}` not recognized'.format(key))


def parse_output(dct, fname=None, fpath=None):
    """parse output struct"""

    if dct is None:
        dct = {}

    # establish defaults
    out = dct.copy()
    if 'path' not in out:
        out['path'] = None
    if 'format' not in out:
        out['format'] = ''
    if 'task_formatter' not in out:
        out['task_formatter'] = '{}'
    if 'force_overwrite' not in out:
        out['force_overwrite'] = True

    fformat = out['format']

    # file name keyword overrides dictionary
    if fname is not None:

        # fname may contain path information
        head, fname = os.path.split(fname)
        if len(head) and fpath is not None:
            raise RuntimeError('contradictory specification')
        elif len(head):
            fpath = head

        fname, ext = os.path.splitext(fname)
        if fformat is None:
            pass
        if ext in fileio.supported and len(fformat):
            fname += ext
        elif ext in fileio.supported:
            fformat = ext

        out['name'] = fname

    # file path keyword overrides dictionary
    if fpath is not None:
        out['path'] = fpath

    # file format
    if fformat is None:
        pass
    elif len(fformat):
        out['format'] = fformat.lstrip('.')
    else:
        out['format'] = 'h5'

    if fformat is None:
        out['file_name'] = None
    else:
        out['file_name'] = '.'.join([out['name'], out['format']])

    return out


def create_solution(dct, verbosity=0):
    """Parse chemistry"""

    assert 'mechanism' in dct, 'missing keyword `mechanism`'

    mech = dct['mechanism']
    path = dct.get('path', '')
    if len(path) == 0:
        xml = mech
    else:
        xml = path.split(os.altsep) + [mech]
        xml = (os.sep).join(xml)
        if self.verbosity > 1:
            print('Loading {}'.format(xml))

    gas = ct.Solution(xml)
    transport = dct.get('transport_model', None)
    if transport is not None:
        gas.transport_model = transport

    return gas


def set_TP(gas, dct, verbosity=0):
    """Set state"""

    # temperature and pressure
    gas.TP = get_value(dct, 'T', 'kelvin'), get_value(dct, 'P', 'pascal')

    return gas


def set_equivalence_ratio(gas, dct, verbosity=0):

    # stoichiometry
    fuel = get_value(dct, 'fuel')
    oxidizer = get_value(dct, 'oxidizer')
    phi = get_value(dct, 'phi', 'dimensionless', enforce=False)
    gas.set_equivalence_ratio(phi, fuel, oxidizer)

    return gas


def update_reactornet_settings(sim, dct, verbosity=0):

    if 'atol' in dct:
        sim.atol = get_value(dct, 'atol', 'seconds', enforce=False)

    if 'rtol' in dct:
        sim.rtol = get_value(dct, 'rtol', 'seconds', enforce=False)

    if 'max_time_step' in dct:
        delta_t_max = get_value(dct, 'max_time_step', 'seconds', enforce=False)
        sim.set_max_time_step(delta_t_max)

    sim.verbose = verbosity > 1
