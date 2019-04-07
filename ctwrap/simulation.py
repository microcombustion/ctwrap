#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reactor objects."""

from __future__ import division, absolute_import, print_function, unicode_literals

import cantera as ct
import pandas as pd
import os
import h5py

from numpy import array

from .configuration import _ReactorBase
from ._helper import get_values

# from .. import tools as zdt


__all__ = ['Simulation']


class _Reactor(_ReactorBase):
    """(Hidden) base class for reactor objects.

    Class implements common access function for 0D reactor networks.

    Specific reactor types are differentiated by overloaded member functions:
       * _create_reactor_network():
       * _advance_reactor_network():
       * _create_dataframe(): set up data frame
       * _append_dataframe(): append output

    All simulation parameters are specified using a dictionary of dictionaries,
    where the intent is to completely specify simulation parameters via YAML input.
    """

    def __init__(self, **kwarg):
        """Constructor"""

        super(_Reactor, self).__init__(**kwarg)

        self.reacting = self.chemistry.get('reacting', True)
        self._dataframe = None
        self.gas = None
        # self.tpx_prev = gas.TPX

        self._t_prev = None
        self._T_prev = None

    @property
    def data(self):
        """Handle to buffered data"""
        return self._dataframe

    # def _get_fuel(self, fuel, blend, fraction, name):

    #     assert fuel is not None, 'information on fuel is missing'

    #     if fuel in self.gas.species_names or fuel in zdt.species_alias():
    #         fuel = zdt.NeatFuel.from_database(fuel)
    #     elif fuel in zdt.list_blends():
    #         fuel = zdt.BlendedFuel.from_recipe(fuel)
    #     else:
    #         raise ValueError('unknown entry for `fuel`')

    #     if blend is None:
    #         out = fuel
    #     else:
    #         if blend in self.gas.species_names or fuel in zdt.species_alias():
    #             blend = zdt.NeatFuel.from_database(blend)
    #         elif blend in zdt.list_blends():
    #             blend = zdt.BlendedFuel.from_recipe(blend)
    #         out = zdt.BlendedFuel.mix(fuel, blend, fraction, name)

    #     return out

    def set_initial_state(self):  # , val=None):
        """Set simulation condition

        Kwargs:
            unique keyword/value pair
        """

        # set up chemistry/geometry/initial
        self._parse_chemistry()

        # temperature, pressure, and composition
        cond = get_values(self.initial)
        self.gas.TP = cond['T_initial'], cond['pressure']
        o2_fraction = .01 * cond['o2_percent']
        oxidizer = 'O2:{}, {}:{}'.format(o2_fraction, cond['diluent'],
                                         1. - o2_fraction)
        # construct fuel
        self.fuel = cond.get('fuel', None)
        if isinstance(self.fuel, str):
            self.gas.set_equivalence_ratio(cond['phi'], self.fuel, oxidizer)
        else:
            self.gas.set_equivalence_ratio(cond['phi'],
                                           self.fuel.x_array(self.gas),
                                           oxidizer)

        # reactor network
        self._create_reactor_network()
        self.delta_t = self.simulation['delta_t']
        self.delta_Tmax = self.simulation.get('delta_Tmax', 25.)
        self.n_points = self.simulation['n_points']

        # update solver parameters
        if 'atol' in self.simulation:
            self._sim.atol = self.simulation['atol']
        if 'rtol' in self.simulation:
            self._sim.rtol = self.simulation['rtol']
        if 'max_time_step' in self.simulation:
            self._sim.set_max_time_step(self.simulation['max_time_step'])

        self._t_prev = [0]
        self._T_prev = [self.gas.T]
        self._points = 1

        self._advance_reactor_network()
        self._create_dataframe()
        self._append_dataframe()

    def advance(self):
        """Advance by default time step"""

        if self._points > 2:

            # predict next point using quadratic extrapolation
            tm2 = self._t_prev[-3] - self._t_prev[-1]
            tm1 = self._t_prev[-2] - self._t_prev[-1]
            fm2 = self._T_prev[-3] - self._T_prev[-1]
            fm1 = self._T_prev[-2] - self._T_prev[-1]
            fp1 = self.delta_Tmax

            # coefficients for quadratic polynomial
            a = fm2 / tm2 - fm1 / tm1
            b = fm1 * tm2 / tm1 - fm2 * tm1 / tm2
            c = fp1 * (tm1 - tm2)

            # find solutions
            if a == 0:
                if b == 0:
                    sol = array([self.delta_t])
                else:
                    sol = array([-c / b])
            else:
                p, q = b / a, c / a
                tmp1 = .25 * p**2 - q  # increasing T
                tmp2 = .25 * p**2 + q  # decreasing T
                if tmp1 < 0:
                    sol = -.5 * p + array([tmp2**.5, -tmp2**.5])
                elif tmp2 < 0:
                    sol = -.5 * p + array([tmp1**.5, -tmp1**.5])
                else:
                    sol = -.5 * p + \
                        array([tmp1**.5, -tmp1**.5, tmp2**.5, -tmp2**.5])

            # find solution with smallest positive step size
            sol = sol[sol > 0]
            if len(sol):
                delta_t = min(sol.min(), self.delta_t)
            else:
                delta_t = self.delta_t

        else:
            # standard step
            delta_t = self.delta_t

        time = self._sim.time + delta_t
        self._sim.advance(time)

        self._t_prev += [time]
        self._T_prev += [self.gas.T]

        update = self._advance_reactor_network()
        self._append_dataframe()

        return update

    def run(self):
        """Run simulation

        Kwargs:
           val (string/int/float): value of varied parameter
        """

        self.set_initial_state()
        self._points = 1

        # loop: note that self.advance() returns boolean
        while self.advance():
            self._points += 1
            if self._points > self.n_points:
                break

    # Hidden functions that need to be overloaded (not intended for direct use)

    def _not_steady_state(self):
        """implement criterion for steady state.

        Re-implementation of cantera's ReactorNet.advance_to_steady_state"""

        atol = self._sim.atol
        rtol = self._sim.rtol

    def _create_reactor_network(self):
        """Create reactor network"""
        raise NotImplementedError('needs to be overloaded')

    def _advance_reactor_network(self):
        """Update reactor parameters."""
        raise NotImplementedError('needs to be overloaded')

    def _create_dataframe(self):
        """Create output data (default behavior is to do nothing)."""
        pass

    def _append_dataframe(self):
        """Append stored data (default behavior is to do nothing)."""
        pass

    # Hidden functions that are likely shared (not intended for direct use)

    def _parse_chemistry(self):
        """Set chemistry (hidden function)"""

        # ensure gas object is set (retrieve if necessary)
        if self.gas is None:

            path = self.chemistry.get('path', None)
            mech = self.chemistry.get('mechanism', None)
            if path is None:
                xml = mech
            else:
                xml = path.split(os.altsep) + [mech]
                xml = (os.sep).join(xml)
            if self.verbosity > 1:
                print('Loading {}'.format(xml))
                # sys.stdout.flush()
            self.gas = ct.Solution(xml)

            transport = self.chemistry.get('transport_model', None)
            if transport is not None:
                self.gas.transport_model = transport

    def _parse_initial(self):
        """Set initial"""

        # temperature and pressure
        cond = self.initial
        self.gas.TP = cond['T_initial'], cond['pressure']

        # stoichiometry
        oxidizer = 'O2:{}, {}:1.'.format(cond['o2_fraction'], cond['diluent'])
        self.gas.set_equivalence_ratio(cond['phi'], cond['fuel'], oxidizer)


###


class Ignition(_Reactor):
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
        super(Ignition, self).__init__(**kwarg)

    def _create_reactor_network(self):
        """Create reactor network (hidden function)

        Set up standard zero-D reactor"""

        # define a flow reactor
        r = ct.IdealGasConstPressureReactor(self.gas)
        r.chemistry_enabled = self.reacting

        # reactor network
        self._sim = ct.ReactorNet([r])

    def _advance_reactor_network(self):
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


class Lagrangian(_Reactor):
    """Lagrangian object handles simulation.

    Attributes:
        chemistry (dict): chemistry specifications
        geometry (dict): reactor geometry
        initial (dict): initial conditions
        profile (dict): temperature profile
        simulation (dict): simulation parameters
        variation (tuple): specifies parameter variation (None if N/A)
        verbosity (int): verbosity level
    """

    def __init__(self,
                 chemistry=None,
                 geometry=None,
                 initial=None,
                 profile=None,
                 simulation=None,
                 output=None,
                 verbosity=0,
                 reacting=True):
        """Constructor of Lagrangian object

        Kwargs:
            geometry (dict): geometry
            chemistry (dict): chemistry
            initial (dict): initial conditions
            simulation (dict): simulation parameters
            verbosity (int): verbosity level
            reacting (bool): enable_reaction
        """

        kwarg = {
            'chemistry': chemistry,
            'geometry': geometry,
            'initial': initial,
            'profile': profile,
            'simulation': simulation,
            'output': output,
            'verbosity': verbosity,
            'reacting': reacting
        }

        # call super
        super(Lagrangian, self).__init__(**kwarg)

        # set up additional reservoirs
        self._ar = ct.Solution('argon.xml')  # using argon for simplicity
        self._air = ct.Solution('air.xml')  # using air for simplicity
        self._tracker = None
        self._profile = None

        # components of reactor network
        self._flow = None
        self._wall = None
        self._env = None
        self._internal = None
        self._external = None

    def _create_reactor_network(self):
        """Create reactor network (hidden function)

        Set up zero-D system (lagrangian particle, wall and ambient,
        with associated heat transfers)"""

        # wall object
        model = self.profile.get('model', None)
        assert model is not None, 'obsolete profile definition'
        obj = {
            'McKenna4parHalf': McKenna4parHalf,
            'Grajetzki2par': Grajetzki2par,
            'Flowreactor7parFull': Flowreactor7parFull,
        }[model]
        self._profile = obj(**self.profile)
        x0 = self._profile.xup
        Tw = self._profile.T(x0)

        # integrator for distance calculation
        initial = get_values(self.initial)
        self._tracker = zd.Distance(x0, initial['T_initial'],
                                    initial['v_initial'])

        # define a flow reactor
        geometry = get_values(self.geometry)
        self._flow = ct.IdealGasConstPressureReactor(self.gas)
        self._flow.chemistry_enabled = self.reacting
        self._flow.volume = geometry['flow_volume']  # 1.e-9 # 1ul

        # define an externally heated reservoir (mimics tube wall) .
        self._ar.TP = Tw, ct.one_atm
        self._wall = ct.IdealGasConstPressureReactor(self._ar)
        self._wall.chemistry_enabled = False
        self._wall.volume = geometry['wall_volume']  # 1.e-5 # 10ml

        # define ambient
        self._env = ct.Reservoir(self._air)

        # inside wall (convective)
        self._internal = ct.Wall(self._wall, self._flow, A=1.)
        Nu = geometry['Nusselt']
        d = geometry['diameter']
        self._internal.heat_transfer_coeff = zd.heat_coeff(self._flow, Nu, d)

        # outside wall (prescribed temperature ... enforce via heat flux)
        self._external = ct.Wall(self._wall, self._env, A=1., U=0.)

        # reactor network
        self._sim = ct.ReactorNet([self._wall, self._flow])

    def _advance_reactor_network(self):
        """Update parameters (hidden)"""

        # advance position
        self._tracker.advance(self._sim.time, self.gas.T)
        v_curr = self._tracker.v
        x_curr = self._tracker.x

        # internal boundary (heat transfer coefficient)
        geometry = get_values(self.geometry)
        Nu = geometry['Nusselt']
        d = geometry['diameter']
        self._internal.heat_transfer_coeff = zd.heat_coeff(self._flow, Nu, d)

        # external boundary (imposed flux)
        heat_flux = zd.heat_transfer(self._wall, self._profile.dTdx(x_curr),
                                     v_curr)
        self._external.set_heat_flux(-heat_flux)

        return self._tracker.x < self._profile.xdn

    def _create_dataframe(self):
        """Create output (using pandas dataframe; hidden)"""

        # create output
        keys = [
            't (s)',
            'z (m)',
            'u (m/s)',
            'Tw (K)',
            'T (K)',
            'rho (kg/m3)',
            'q',
        ] + self.gas.species_names
        self._dataframe = pd.DataFrame(columns=keys)

        # verbose output
        if self.verbosity > 1:
            print('%10s %10s %10s %14s' % ('t [s]', 'T [K]', 'P [Pa]',
                                           'u [J/kg]'))

    def _append_dataframe(self):
        """Append data (using pandas dataframe; hidden)"""

        heat_release = -self.gas.standard_enthalpies_RT.dot(
            self.gas.net_production_rates) * ct.gas_constant * self.gas.T
        # alternative
        # heat_release = -self.gas.net_rates_of_progress.dot(
        #     self.gas.delta_enthalpy)

        df_len = len(self.data)
        row = (self._sim.time, self._tracker.x, self._tracker.v,
               self._profile.T(self._tracker.x), self.gas.T, self.gas.density,
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
