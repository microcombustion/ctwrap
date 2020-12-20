"""Simulation module running ignition test

Code is based on stock Cantera example `reactor1.py
<https://cantera.org/examples/python/reactors/reactor1.py.html>`_,
where differences are:

* Parameter values are passed using a :any:`Parser` object
* Content is broken down into methods ``defaults`` and ``run``
"""
import warnings

from ctwrap import Parser


# pylint: disable=no-member
try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)


def defaults():
    """Returns Parser object containing default configuration"""
    return Parser.from_yaml('ignition.yaml', defaults=True)


def run(name, chemistry=None,
        initial=None, simulation=None):
    """Function handling reactor simulation.

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        name (str): output group name
        chemistry  (Parser): overloads 'defaults.chemistry'
        initial    (Parser): overloads 'defaults.initial'
        simulation (Parser): overloads 'defaults.simulation'

    Returns:
        Dictionary containing Cantera SolutionArray
    """

    # initialize gas object
    gas = ct.Solution(chemistry.mechanism)

    # set temperature, pressure, and composition
    T = initial.T.m_as('kelvin')
    P = initial.P.m_as('pascal')
    gas.TP = T, P
    phi = initial['phi']
    gas.set_equivalence_ratio(phi, initial['fuel'], initial['oxidizer'])

    # define a reactor network
    reactor = ct.IdealGasConstPressureReactor(gas)
    sim = ct.ReactorNet([reactor])

    delta_T_max = 20.
    reactor.set_advance_limit('temperature', delta_T_max)

    # set simulation parameters
    sim.atol = simulation['atol']
    sim.rtol = simulation['rtol']
    delta_t = simulation['delta_t']
    n_points = simulation['n_points']

    # define SolutionArray and run simulation
    states = ct.SolutionArray(gas, extra=['t'])
    time = sim.time

    for _ in range(n_points):

        time += delta_t
        sim.advance(time)
        states.append(reactor.thermo.state, t=time)

    return {name: states}


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
