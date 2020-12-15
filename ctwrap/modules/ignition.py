"""Simulation module running ignition test

Code is based on stock Cantera example:
https://cantera.org/examples/python/reactors/reactor1.py.html

Differences between stock cantera example and ctwrap version are:

* Content is broken down into methods to load values, run the simulation, and save output
"""
import warnings
from ruamel import yaml


# pylint: disable=no-member
try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)


# define default values for simulation parameters (specified as list)
DEFAULTS = """\
# default parameters for the `ignition` module
initial:
  T: 1000. # temperature (kelvin)
  P: 101325. # pressure (Pascal)
  phi: 1. # equivalence ratio
  fuel: H2
  oxidizer: O2:1.,AR:3.76
chemistry:
  mechanism: h2o2.yaml
simulation:
  delta_t: 1.e-5
  n_points: 500
  atol: 1.e-15
  rtol: 1.e-9
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(DEFAULTS, Loader=yaml.SafeLoader)


def run(name, chemistry=None,
        initial=None, simulation=None):
    """
    Function handling reactor simulation.

    Arguments:
        name (str): output group name
        chemistry  (dict): reflects yaml 'configuration:chemistry'
        initial    (dict): reflects yaml 'configuration:initial'
        simulation (dict): reflects yaml 'configuration:simulation'

    Returns:
        Dictionary containing Cantera SolutionArray
    """

    # initialize gas object
    mech = chemistry['mechanism']
    gas = ct.Solution(mech)

    # set temperature, pressure, and composition
    T = initial['T']
    P = initial['P']
    gas.TP = T, P
    phi = initial['phi']
    gas.set_equivalence_ratio(phi, initial['fuel'], initial['oxidizer'])

    # define a reactor network
    reactor = ct.IdealGasConstPressureReactor(gas)
    sim = ct.ReactorNet([reactor])

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


def save(filename, data, task=None, **kwargs):
    """
    This function saves the output from the run method

    Arguments:
        filename (str): naming of file
        data (dict): data to be saved
        task (str): name of task if running variations
        kwargs (dict): keyword arguments
    """

    # todo: implement subgroup for higher dimensional space

    attrs = {'description': task}
    for group, states in data.items():
        states.write_hdf(filename=filename, group=group,
                         attrs=attrs, **kwargs)


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
    save('ignition.h5', out)
