"""Simulation module running an equilibrium test for a fuel/air mixture

Code is based on stock Cantera example `multiphase/adiabatic.py
<https://cantera.org/examples/python/multiphase/adiabatic.py.html>`_,
where differences are:

* Parameter values are passed using a :any:`Parser` object
* Content is broken down into methods ``defaults`` and ``run``
"""
import warnings
import pandas as pd

from ctwrap import Parser


try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)


def defaults():
    """Returns Parser object containing default configuration"""
    return Parser.from_yaml('equilibrium.yaml', defaults=True)


def run(initial, phases, equilibrate, returns):

    # phases that will be included in the calculation, and their initial moles
    mix_phases = []
    for phase in phases.values():
        ph = ct.Solution(phase.mechanism)
        if all([key in phase for key in ['fuel', 'oxidizer', 'phi']]):
            ph.set_equivalence_ratio(phase.phi, phase.fuel, phase.oxidizer)
        elif 'X' in phase:
            ph.X = phase.X
        elif 'Y' in phase:
            ph.Y = phase.Y
        mix_phases.append((ph, phase.moles))

    # equilibrate the mixture adiabatically at constant P
    print(mix_phases)
    mix = ct.Mixture(mix_phases)
    mix.T = initial.T.m_as('kelvin')
    mix.P = initial.P.m_as('pascal')
    mix.equilibrate(
        equilibrate.mode, solver=equilibrate.solver,
        max_steps=equilibrate.max_steps)

    tad = mix.T
    print('At phi = {0:12.4g}, Tad = {1:12.4g}'.format(phases.gas.phi, tad))

    out = []
    for k, v in returns.items():
        value = getattr(mix, str(v))
        if hasattr(mix, k) and isinstance(getattr(mix, k), list):
            out.extend(zip(getattr(mix, k), value))
        else:
            out.append((k, value))

    return pd.Series(out)


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
