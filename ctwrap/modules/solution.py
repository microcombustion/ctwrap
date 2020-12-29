"""Simulation module querying properties of a Cantera ``Solution`` object

This module mainly serves for illustration purposes; it is more
efficient to use Cantera's ``Solution`` and ``SolutionArray`` objects
directly within a Python environment.
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
    state = {
        'T': '300. kelvin',
        'P': '1. atmosphere',
        'X': 'H2:1.,O2:1'
    }
    return Parser({'mechanism': 'h2o2.yaml', 'state': state})


def run(mechanism, state):
    """Function setting state of Cantera ``Solution`` object.

    Queried values are handled by the ``ctwrap``, where the YAML field
    ``output.returns`` specifies what values are written to file.
    """
    T = state.T.m_as('kelvin')
    P = state.P.m_as('pascal')

    obj = ct.Solution(mechanism)
    if all([key in state for key in ['fuel', 'oxidizer', 'phi']]) :
        obj.TP = T, P
        obj.set_equivalence_ratio(state.phi, state.fuel, state.oxidizer)
    elif 'X' in state:
        obj.TPX = T, P, state.X
    elif 'Y' in state:
        obj.TPY = T, P, state.Y

    return obj


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
