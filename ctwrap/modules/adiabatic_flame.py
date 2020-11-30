#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ruamel import yaml

from ctwrap import Parser

import warnings
try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)

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
        name (str): name of the task

    Keyword Arguments:
        chemistry (dict): reflects yaml 'configuration:chemistry'
        upstream  (dict): reflects yaml 'configuration:upstream'
        domain    (dict): reflects yaml 'configuration:simulation'
        loglevel   (int): amount of diagnostic output (0 to 8)

    Returns:
        Out (dict): dictionary containing cantera Flamebase object

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.
    """

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

    out = {}

    # Solve with mixture-averaged transport model
    f.transport_model = 'Mix'
    f.solve(loglevel=loglevel, auto=True)

    # Solve with the energy equation enabled
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: mixture-averaged flamespeed = {1:7f} m/s'
    print(msg.format(name, f.velocity[0]))

    if name is not 'defaults':
        group = name + "<mix>"
    else:
        group = "mix"
    out[group] = f

    # Solve with multi-component transport properties
    f.transport_model = 'Multi'
    f.solve(loglevel)  # don't use 'auto' on subsequent solves
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: multi-component flamespeed  = {1:7f} m/s'
    print(msg.format(name, f.velocity[0]))

    if name is not 'defaults':
        group = name + "<multi>"
    else:
        group = "multi"
    out[group] = f

    return out

###


if __name__ == "__main__":

    config = defaults()
    df = run('main', **config, loglevel=1)
