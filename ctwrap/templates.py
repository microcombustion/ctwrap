#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Objects handling simulations."""

import cantera as ct
import pandas as pd
import os

from numpy import array

from .configuration import Configuration
from ._helper import get_values

__all__ = ['Template', 'ZeroD']


class _Base(Configuration):
    """Rudimentary functions required by a simulation object"""

    def __init__(self, verbosity=0, **kwargs):
        """Hidden constructor

        Kwargs:
           verbosity (int): verbosity level
           plus keywords to be mapped to attributes.
        """

        super().__init__(**kwargs)

        self.verbosity = verbosity
        self._dataframe = None

    @property
    def verbose(self):
        """Verbosity level"""
        return self.verbosity > 0

    @property
    def data(self):
        """Handle to buffered data"""
        return self._dataframe

    def initialize(self):
        """Initialize the simulation"""
        if self.verbosity > 0:
            print('Class method `initialize` needs '
                  'to be overloaded: do nothing')
        return False

    def run(self):
        """Run the simulation"""
        if self.verbosity > 0:
            print('Class method `run` needs to be overloaded: do nothing')
        return False

    def save(self, key, oname, path='.'):
        """Save data frame
        """

        df = self._dataframe
        if df is None or len(df) == 0:
            if self.verbosity > 0:
                print('No data available: do nothing')
            return

        # output is usually configured in yaml file
        output = self._config.get('output', {})

        # species to save
        save_species = output.get('save_species', True)
        if isinstance(save_species, [tuple, list]):
            keys = [k for k in df.keys() if k not in self.gas.species_names]
            keys += [k for k in save_species]
        elif save_species == True:
            keys = [k for k in df.keys()]
        elif save_species == False:
            keys = [k for k in df.keys() if k not in self.gas.species_names]
        else:
            raise ValueError('incompatible species information')

        # file format
        fname = (os.sep).join([path, oname])
        fmt = output.get('format', 'h5')
        if fmt in ['hdf', 'h5', 'hdf5']:

            # HDF5 container format
            df[keys].to_hdf(fname, key, mode='a', complib='bzip2')

        elif fmt in ['xlsx']:

            # Excel
            with ExcelWriter(fname, engine='openpyxl', mode='a') as writer:
                df[keys].to_excel(writer, sheet_name=key)

        elif fmt in ['csv']:

            # comma separated files
            raise NotImplementedError('@todo')

        else:

            raise NotImplementedError(
                'output as `.{}` is not implemented'.format(fmt))


class Template(_Base):
    """Base class for simulation objects.

    Class implements common access function for simulations.

    Specific reactor types are differentiated by overloaded member functions:
       * _create_dataframe(): set up data frame
       * _append_dataframe(): append output

    All simulation parameters are specified using a dictionary of dictionaries,
    where the intent is to completely specify simulation parameters via YAML input.
    """

    def __init__(self, **kwarg):
        """Constructor"""

        super().__init__(**kwarg)

        self.reacting = self.chemistry.get('reacting', True)
        self.gas = None

    def _create_dataframe(self):
        """Create output data (default behavior is to do nothing)."""
        pass
        # raise NotImplementedError('needs to be overloaded')

    def _append_dataframe(self):
        """Append stored data (default behavior is to do nothing)."""
        pass
        # raise NotImplementedError('needs to be overloaded')


class ZeroD(Template):
    """Base class for zero-dimensional simulation objects.

    Class implements common access function for 0D reactor networks.

    Specific reactor types are differentiated by overloaded member functions:
       * _create_reactor_network():
       * _advance_reactor_network():
       * _update_reactor_network(): 

    All simulation parameters are specified using a dictionary of dictionaries,
    where the intent is to completely specify simulation parameters via YAML input.
    """

    def __init__(self, **kwarg):
        """Constructor"""

        super().__init__(**kwarg)

        self.reacting = self.chemistry.get('reacting', True)
        self.gas = None

        self._t_prev = None
        self._T_prev = None

    def initialize(self):  # , val=None):
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

        self._update_reactor_network()
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

        update = self._update_reactor_network()
        self._append_dataframe()

        return update

    def run(self):
        """Run simulation

        Kwargs:
           val (string/int/float): value of varied parameter
        """

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

    def _update_reactor_network(self):
        """Update reactor parameters."""
        raise NotImplementedError('needs to be overloaded')

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
