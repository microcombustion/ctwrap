#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cantera as ct
import pandas as pd
import numpy as np

from ctwrap.fileio import load_yaml
from ctwrap import parsers


def freeflame(name,
              verbosity=0,
              chemistry=None,
              upstream=None,
              domain=None,
              loglevel=0):
    """Function handling reactor simulation.

    Arguments:
        name (str): name used for output

    Keyword Arguments:
        verbosity (bool): verbosity level (required)
        chemistry (dict): reflects yaml 'configuration:chemistry'
        upstream  (dict): reflects yaml 'configuration:upstream'
        domain    (dict): reflects yaml 'configuration:simulation'
        loglevel   (int): amount of diagnostic output (0 to 8)

    Returns:
        dict: dictionary with pandas DataFrame entries
    """

    out = {}

    # initialize

    # IdealGasMix object used to compute mixture properties, set to the state of the
    # upstream fuel-air mixture
    gas = parsers.create_solution(chemistry)

    # temperature, pressure, and composition
    parsers.set_TP(gas, upstream)
    parsers.set_equivalence_ratio(gas, upstream)

    width = parsers.get_value(domain, 'width', 'meter')

    # entries used for output
    keys = ['z (m)', 'u (m/s)', 'V (1/s)', 'T (K)', 'rho (kg/m3)'] + \
        gas.species_names

    # Set up flame object
    f = ct.FreeFlame(gas, width=width)
    f.set_refine_criteria(ratio=3, slope=0.06, curve=0.12)
    if loglevel > 0:
        f.show_solution()

    # Solve with mixture-averaged transport model
    f.transport_model = 'Mix'
    f.solve(loglevel=loglevel, auto=True)

    # Solve with the energy equation enabled
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: mixture-averaged flamespeed = {1:7f} m/s'
    print(msg.format(name, f.u[0]))

    out[name + ':mix'] = pd.DataFrame(
        np.vstack([f.grid, f.u, f.V, f.T, f.density, f.X]).T, columns=keys)

    # Solve with multi-component transport properties
    f.transport_model = 'Multi'
    f.solve(loglevel)  # don't use 'auto' on subsequent solves
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: multi-component flamespeed  = {1:7f} m/s'
    print(msg.format(name, f.u[0]))

    out[name + ':multi'] = pd.DataFrame(
        np.vstack([f.grid, f.u, f.V, f.T, f.density, f.X]).T, columns=keys)

    return out


###

if __name__ == "__main__":

    config = load_yaml('freeflame.yaml')
    df = freeflame('main', **config, loglevel=1)
