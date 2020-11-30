#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cantera as ct
from ruamel import yaml
import pandas as pd


from ctwrap import Parser

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


def run(name, chemistry=None, initial=None,
        simulation=None, **kwargs):
    """Function handling reactor simulation.
    Args:
        name (str): name of the task

    Keyword Arguments:
        chemistry  (dict): reflects yaml 'configuration:chemistry'
        initial    (dict): reflects yaml 'configuration:initial'
        simulation (dict): reflects yaml 'configuration:simulation'


    Returns:
        out (dict): dictionary containing SolutionArray

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

    # SolutionArray
    states = ct.SolutionArray(gas, extra=['t'])

    # Run simulation
    time = sim.time

    # loop: note that advance() returns boolean
    for i in range(n_points):

        time += delta_t
        sim.advance(time)

        states.append(reactor.thermo.state, t=time)

    out = {}
    out[name] = states

    return out


###

if __name__ == "__main__":
    config = defaults()
    out = run('main', **config)
