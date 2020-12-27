"""Simulation module running adiabatic flame test

Code is based on stock Cantera example `adiabatic_flame.py
<https://cantera.org/examples/python/onedim/adiabatic_flame.py.html>`_,
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
    return Parser.from_yaml('adiabatic_flame.yaml', defaults=True)


def run(model=None, upstream=None, domain=None, settings=None):
    """Function handling adiabatic flame simulation.

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        model    (Parser): overloads 'defaults.model'
        upstream (Parser): overloads 'defaults.upstream'
        domain   (Parser): overloads 'defaults.simulation'
        settings (Parser): overloads 'defaults.settings'

    Returns:
        Dictionary containing Cantera `FlameBase` object
    """

    # initialize

    # IdealGasMix object used to compute mixture properties, set to the state of the
    # upstream fuel-air mixture
    gas = ct.Solution(model.mechanism)

    # temperature, pressure, and composition
    T = upstream.T.m_as('kelvin')
    P = upstream.P.m_as('pascal')
    gas.TP = T, P
    phi = upstream.phi
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)

    # set up flame object
    width = domain.width.m_as('meter')
    f = ct.FreeFlame(gas, width=width)
    f.set_refine_criteria(ratio=settings.ratio, slope=settings.slope, curve=settings.curve)
    if settings.loglevel > 0:
        f.show_solution()

    # Solve with mixture-averaged transport model
    f.transport_model = 'Mix'
    f.solve(loglevel=settings.loglevel, auto=True)

    # Solve with the energy equation enabled
    if settings.loglevel > 0:
        f.show_solution()
    msg = '    mixture-averaged flamespeed = {:7f} m/s'
    print(msg.format(f.velocity[0]))

    f_sol = f.to_solution_array()

    # Solve with multi-component transport properties
    gas.TP = T, P
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)
    g = ct.FreeFlame(gas, width=width)
    g.set_initial_guess(data=f_sol)
    g.transport_model = 'Multi'
    g.solve(settings.loglevel)  # don't use 'auto' on subsequent solves
    if settings.loglevel > 0:
        g.show_solution()
    msg = '    multi-component flamespeed  = {:7f} m/s'
    print(msg.format(g.velocity[0]))

    return {'mix': f, 'multi': g}


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
