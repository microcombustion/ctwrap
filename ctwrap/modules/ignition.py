#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cantera as ct
import pandas as pd

from ctwrap.fileio import load_yaml
from ctwrap import parsers


def ignition(name, chemistry=None, initial=None, simulation=None, verbosity=0):
    """Function handling reactor simulation.

    Keyword Arguments:
        chemistry  (dict): reflects yaml 'configuration:chemistry'
        initial    (dict): reflects yaml 'configuration:initial'
        simulation (dict): reflects yaml 'configuration:simulation'
        verbosity  (bool): verbosity level (required)
    """

    # initialize

    gas = parsers.create_solution(chemistry)

    # temperature, pressure, and composition
    parsers.set_TP(gas, initial)
    parsers.set_equivalence_ratio(gas, initial)

    # define a reactor network
    reactor = ct.IdealGasConstPressureReactor(gas)
    sim = ct.ReactorNet([reactor])
    parsers.update_reactornet_settings(sim, simulation)

    # settings for reactor advancement
    delta_t = parsers.get_value(
        simulation, 'delta_t', 'seconds', enforce=False)
    n_points = parsers.get_value(simulation, 'n_points')

    # preprocess

    # create pandas data frame
    keys = ['t (s)', 'T (K)', 'rho (kg/m3)', 'q'] + \
        gas.species_names
    df = pd.DataFrame(columns=keys)

    # Run simulation

    time = sim.time

    # loop: note that advance() returns boolean
    for i in range(n_points):

        time += delta_t
        sim.advance(time)

        heat_release = -gas.standard_enthalpies_RT.dot(
            gas.net_production_rates) * ct.gas_constant * gas.T
        # alternative
        # heat_release = -gas.net_rates_of_progress.dot(
        #     gas.delta_enthalpy)

        df_len = len(df)
        row = (time, gas.T, gas.density, heat_release) + tuple(gas.X)
        df.loc[df_len] = row

    return {name: df}


###

if __name__ == "__main__":

    config = load_yaml('ignition.yaml')
    df = ignition('main', **config)
