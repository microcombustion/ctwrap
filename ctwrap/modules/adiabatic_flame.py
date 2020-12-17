"""Simulation module running adiabatic flame test

Code is based on stock Cantera example:
https://cantera.org/examples/python/onedim/adiabatic_flame.py.html

Differences between stock cantera example and ctwrap version are:

* Parameter values are passed using a `Parser` object (equivalent to dictionary)
* Content is broken down into methods to load values, run the simulation, and save output
"""
import warnings

from ctwrap import Parser


try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)


# define default values for simulation parameters (string notation)
DEFAULTS = """\
# default parameters for the `adiabatic_flame` module
upstream:
  T: 300. kelvin # temperature
  P: 1. atmosphere # pressure
  phi: .55 # equivalence ratio
  fuel: H2
  oxidizer: O2:1.,AR:5
chemistry:
  mechanism: h2o2.yaml
domain:
  width: 30 millimeter # domain width
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return Parser.from_yaml(DEFAULTS)


def run(name, chemistry=None, upstream=None, domain=None, loglevel=0):
    """
    Function handling adiabatic flame simulation.
    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        name (str): output group name
        chemistry (Parser): reflects yaml 'configuration:chemistry'
        upstream  (Parser): reflects yaml 'configuration:upstream'
        domain    (Parser): reflects yaml 'configuration:simulation'
        loglevel   (int): amount of diagnostic output (0 to 8)

    Returns:
        Dictionary containing Cantera `Flamebase` object
    """

    # initialize

    # IdealGasMix object used to compute mixture properties, set to the state of the
    # upstream fuel-air mixture
    gas = ct.Solution(chemistry.mechanism)

    # temperature, pressure, and composition
    T = upstream.T.m_as('kelvin')
    P = upstream.P.m_as('pascal')
    gas.TP = T, P
    phi = upstream.phi
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)

    # set up flame object
    width = domain.width.m_as('meter')
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

    group = name + "_mix"
    out[group] = f

    f_sol = f.to_solution_array()

    # Solve with multi-component transport properties
    gas.TP = T, P
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)
    g = ct.FreeFlame(gas, width=width)
    g.set_initial_guess(data=f_sol)
    g.transport_model = 'Multi'
    g.solve(loglevel)  # don't use 'auto' on subsequent solves
    if loglevel > 0:
        g.show_solution()
    msg = '    {0:s}: multi-component flamespeed  = {1:7f} m/s'
    print(msg.format(name, g.velocity[0]))

    group = name + "_multi"
    out[group] = g

    return out


def save(filename, data, task=None, **kwargs):
    """
    This function saves the output from the run method

    Arguments:
        filename (str): naming of file
        data (Dict): data to be saved
        task (str): name of task if running variations
        kwargs (dict): keyword argument
    """

    for group, flame in data.items():
        flame.write_hdf(filename=filename, group=group,
                        description=task, **kwargs)


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    df = run('main', **config, loglevel=1)
    save('adiabatic_flame.h5', df)
