#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ctwrap import ZeroD


class Ignition(ZeroD):
    """Lagrangian object handles simulation.

    Attributes:
        chemistry (dict): chemistry specifications
        initial (dict): initial conditions
        simulation (dict): simulation parameters
        variation (tuple): specifies parameter variation (None if N/A)
        verbosity (int): verbosity level
    """

    def __init__(self,
                 chemistry=None,
                 initial=None,
                 simulation=None,
                 output=None,
                 verbosity=0,
                 reacting=True):
        """Constructor of Ignition object

        Kwargs:
            chemistry (dict): chemistry
            initial (dict): initial conditions
            simulation (dict): simulation parameters
            verbosity (int): verbosity level
            reacting (bool): enable_reaction
        """

        kwarg = {
            'chemistry': chemistry,
            'initial': initial,
            'simulation': simulation,
            'output': output,
            'verbosity': verbosity
        }

        # call super
        super().__init__(**kwarg)

    def _create_reactor_network(self):
        """Create reactor network (hidden function)

        Set up standard zero-D reactor"""

        # define a flow reactor
        r = ct.IdealGasConstPressureReactor(self.gas)
        r.chemistry_enabled = self.reacting

        # reactor network
        self._sim = ct.ReactorNet([r])

    def _update_reactor_network(self):
        """Update reactor parameters."""

        return True

    def _create_dataframe(self):
        """Create output data."""

        # create output
        keys = ['t (s)', 'T (K)', 'rho (kg/m3)', 'q'] + self.gas.species_names
        self._dataframe = pd.DataFrame(columns=keys)

        # verbose output
        if self.verbosity > 1:
            print('%10s %10s %10s %14s' % ('t [s]', 'T [K]', 'P [Pa]',
                                           'u [J/kg]'))

    def _append_dataframe(self):
        """Append stored data."""

        heat_release = -self.gas.standard_enthalpies_RT.dot(
            self.gas.net_production_rates) * ct.gas_constant * self.gas.T
        # alternative
        # heat_release = -self.gas.net_rates_of_progress.dot(
        #     self.gas.delta_enthalpy)

        df_len = len(self.data)
        row = (self._sim.time, self.gas.T, self.gas.density,
               heat_release) + tuple(self.gas.X)
        self.data.loc[df_len] = row

        # verbose output
        if self.verbosity > 1:
            print('%10.3e %10.3f %10.3f %14.6e' % (
                self._sim.time,
                self._flow.T,
                self._flow.thermo.P,
                self._flow.thermo.u,
            ))


###
