"""Simulation module running adiabatic flame test

Code is based on stock Cantera example `adiabatic_flame.py
<https://cantera.org/examples/python/onedim/adiabatic_flame.py.html>`_,
where differences are:

* Parameter values are passed using a :any:`Parser` object
* Content is broken down into methods ``defaults`` and ``run``
"""
import warnings

from ctwrap import Parser


try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)


def defaults():
    """Returns Parser object containing default configuration"""
    return Parser.from_yaml('adiabatic_flame.yaml', defaults=True)


def run(name, chemistry=None, upstream=None, domain=None, loglevel=0):
    """Function handling adiabatic flame simulation.

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        name (str): output group name
        chemistry (Parser): overloads 'defaults.chemistry'
        upstream  (Parser): overloads 'defaults.upstream'
        domain    (Parser): overloads 'defaults.simulation'
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
