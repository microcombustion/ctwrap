#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ruamel import yaml
import cantera as ct
import pandas as pd
import numpy as np

from ctwrap import Parser

__DEFAULTS = """\
# default parameters for the `freeflame` module
upstream:
  T: [300., kelvin, 'temperature']
  P: [1., atmosphere, 'pressure']
  phi: [.55, dimensionless, 'equivalence ratio']
  fuel: 'H2'
  oxidizer: 'O2:1.,AR:5'
chemistry:
  mechanism: h2o2.xml
domain:
  width: [30, millimeter, 'domain width']
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name,
        chemistry=None,
        upstream=None,
        domain=None,
        loglevel=0):
    """Function handling reactor simulation.

    Arguments:
        name (str): name used for output

    Keyword Arguments:
        chemistry (dict): reflects yaml 'configuration:chemistry'
        upstream  (dict): reflects yaml 'configuration:upstream'
        domain    (dict): reflects yaml 'configuration:simulation'
        loglevel   (int): amount of diagnostic output (0 to 8)

    Returns:
        dict: dictionary with pandas DataFrame entries

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.
    """

    out = {}

    # initialize

    # IdealGasMix object used to compute mixture properties, set to the state of the
    # upstream fuel-air mixture
    mech = Parser(chemistry).mechanism
    gas = ct.Solution(mech)

    # temperature, pressure, and composition
    upstream = Parser(upstream)
    T = upstream.T.m_as('kelvin')
    P = upstream.P.m_as('pascal')
    gas.TP = T, P
    phi = upstream.phi.m
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)

    # set up flame object
    width = Parser(domain).width.m_as('meter')
    f = ct.FreeFlame(gas, width=width)
    f.set_refine_criteria(ratio=3, slope=0.06, curve=0.12)
    if loglevel > 0:
        f.show_solution()

    # entries used for output
    keys = ['z (m)', 'u (m/s)', 'V (1/s)', 'T (K)', 'rho (kg/m3)'] + \
        gas.species_names

    # Solve with mixture-averaged transport model
    f.transport_model = 'Mix'
    f.solve(loglevel=loglevel, auto=True)

    # Solve with the energy equation enabled
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: mixture-averaged flamespeed = {1:7f} m/s'
    print(msg.format(name, f.u[0]))

    out[name + '<mix>'] = pd.DataFrame(
        np.vstack([f.grid, f.u, f.V, f.T, f.density, f.X]).T, columns=keys)

    # Solve with multi-component transport properties
    f.transport_model = 'Multi'
    f.solve(loglevel)  # don't use 'auto' on subsequent solves
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: multi-component flamespeed  = {1:7f} m/s'
    print(msg.format(name, f.u[0]))

    out[name + '<multi>'] = pd.DataFrame(
        np.vstack([f.grid, f.u, f.V, f.T, f.density, f.X]).T, columns=keys)

    return out


###

if __name__ == "__main__":

    config = defaults()
    df = run('main', **config, loglevel=1)
