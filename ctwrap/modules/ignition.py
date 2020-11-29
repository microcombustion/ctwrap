#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from ruamel import yaml

from ctwrap import Parser

import warnings
try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)

# default configuration
__DEFAULTS = """\
# default parameters for the `ignition` module
initial:
  T: [1000., kelvin, 'temperature']
  P: [1., atmosphere, 'pressure']
  phi: [1., dimensionless, 'equivalence ratio']
  fuel: 'H2'
  oxidizer: 'O2:1.,AR:3.76'
chemistry:
  mechanism: h2o2.xml
simulation:
  delta_t: 1.e-5
  n_points: 500
  atol: 1.e-15
  rtol: 1.e-9
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name, chemistry=None, initial=None, simulation=None):
    """Function handling reactor simulation.

    Keyword Arguments:
        chemistry  (dict): reflects yaml 'configuration:chemistry'
        initial    (dict): reflects yaml 'configuration:initial'
        simulation (dict): reflects yaml 'configuration:simulation'

    Returns:
        dict: dictionary with pandas DataFrame entries

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.
    """

    # initialize

    # gas object
    mech = Parser(chemistry).mechanism
    gas = ct.Solution(mech)

    # temperature, pressure, and composition
    initial = Parser(initial)
    T = initial.T.m_as('kelvin')
    P = initial.P.m_as('pascal')
    gas.TP = T, P
    phi = initial.phi.m
    gas.set_equivalence_ratio(phi, initial.fuel, initial.oxidizer)

    # define a reactor network
    reactor = ct.IdealGasConstPressureReactor(gas)
    sim = ct.ReactorNet([reactor])

    # set simulation parameters
    par = Parser(simulation)
    sim.atol = par.atol
    sim.rtol = par.rtol
    delta_t = par.delta_t
    n_points = par.n_points

    # preprocess

    # create pandas data frame
    keys = ['t (s)', 'T (K)', 'rho (kg/m3)'] + \
        gas.species_names
    df = pd.DataFrame(columns=keys)

    # Run simulation

    time = sim.time

    # loop: note that advance() returns boolean
    for i in range(par.n_points):

        time += delta_t
        sim.advance(time)

        df_len = len(df)
        row = (time, gas.T, gas.density) + tuple(gas.X)
        df.loc[df_len] = row

    return {name: df}


###

if __name__ == "__main__":

    config = defaults()
    out = run('main', **config)
