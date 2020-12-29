"""Simulation module running an equilibrium test for a fuel/air mixture

Code is based on stock Cantera example `multiphase/adiabatic.py
<https://cantera.org/examples/python/multiphase/adiabatic.py.html>`_,
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
    return Parser.from_yaml('equilibrium.yaml', defaults=True)


def run(initial, phases, equilibrate):
    """Function handling equilibrium calculations.

    The function handles equilibrium calculations for both single
    phases (``Solution``; single entry in *phases* argument) and multiple
    phases (``Mixture``; multiple entries in *phases* argument).

    Arguments:
        initial (Parser): Initial condition
        phases (Parser): Definition of phases
        equilibrate (Parser): Arguments of ``equilibrate`` function

    Returns:
        Cantera `Solution` or `Mixture` object
    """
    T = initial.T.m_as('kelvin')
    P = initial.P.m_as('pascal')

    # phases that will be included in the calculation, and their initial moles
    mix_phases = []
    for phase in phases.values():
        if phase is None:
            continue
        obj = ct.Solution(phase.mechanism)
        if all([key in phase for key in ['fuel', 'oxidizer']] + ['phi' in initial]) :
            obj.TP = T, P
            obj.set_equivalence_ratio(initial.phi, phase.fuel, phase.oxidizer)
        elif 'X' in phase:
            obj.TPX = T, P, phase.X
        elif 'Y' in phase:
            obj.TPY = T, P, phase.Y
        mix_phases.append((obj, phase.get('moles')))

    # equilibrate the mixture based on configuration
    if len(mix_phases) > 1:
        obj = ct.Mixture(mix_phases)
        obj.T = T
        obj.P = P
    kwargs = equilibrate.raw
    mode = kwargs.pop('mode')
    obj.equilibrate(mode, **kwargs)

    print('Tad = {:8.2f}'.format(obj.T))

    return obj


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
