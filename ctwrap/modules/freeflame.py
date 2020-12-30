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
    ct = ImportError('Method requires a working cantera installation.')


def defaults():
    """Returns Parser object containing default configuration"""
    return Parser.from_yaml('freeflame.yaml', defaults=True)


def restart(base, **kwargs):
    """Restart calculation"""
    return run(restart=base, **kwargs)


def run(model=None, upstream=None, domain=None, settings=None, restart=None):
    """Function handling adiabatic flame simulation.

    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        model    (Parser): overloads 'defaults.model'
        upstream (Parser): overloads 'defaults.upstream'
        domain   (Parser): overloads 'defaults.simulation'
        settings (Parser): overloads 'defaults.settings'
        restart (ct.FlameBase): previous solution

    Returns:
        Cantera `FlameBase` object
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

    if restart:
        f = restart
        f.P = P
        f.inlet.T = T
        f.inlet.X = gas.X
        auto = False
    else:
        # set up flame object
        width = domain.width.m_as('meter')
        f = ct.FreeFlame(gas, width=width)
        auto = True
        if model.transport.lower() != 'mix':
            raise ValueError("Initial simulation should use mixture-averaged transport")

    f.set_refine_criteria(ratio=settings.ratio, slope=settings.slope, curve=settings.curve)
    if model.transport.lower() == 'soret':
        f.transport_model = 'Multi'
        f.soret_enabled = True
    else:
        f.transport_model = model.transport.capitalize()

    # Solve with mixture-averaged transport model
    f.solve(loglevel=settings.loglevel, auto=auto)

    # Solve with the energy equation enabled
    msg = '    flamespeed = {:7f} m/s ({})'
    print(msg.format(f.velocity[0], model.transport))
    return f


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
