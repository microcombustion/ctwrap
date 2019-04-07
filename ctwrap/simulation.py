#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Object handling variations."""

import os
import pandas as pd
from copy import deepcopy

# multiprocessing
import multiprocessing as mp
import queue  # imported for using queue.Empty exception

from ._helper import flatten, load_yaml
from .templates import _Base

__all__ = ['SimulationHandler']


def worker(tasks_to_accomplish, tasks_that_are_done, simulation, lock, var0,
           hdf_args):

    verbosity = hdf_args.get('verbosity', False)
    this = mp.current_process().name

    # check compliance of target object
    for m in ['__init__', 'run', 'save']:
        msg = 'Target object is missing required method `{}`'
        assert hasattr(simulation, m), msg.format(m)

    if verbosity > 1:
        print('starting ' + this)

    while True:
        try:
            # retrieve next simulation task
            key, config = tasks_to_accomplish.get_nowait()
            if verbosity > 1:
                print('fetching next case: `{}`'.format(key))

        except queue.Empty:
            # no tasks left
            if verbosity > 1:
                print('terminating ' + this)
            break

        else:
            # perform task
            obj = simulation(**config)
            if verbosity > 0:
                pvar, kvar = var0
                msg = ' * processing `{}.{}`: {} ({})'
                print(msg.format(pvar, kvar, key, this))
            obj.initialize()
            obj.run()
            with lock:
                key_str = hdf_args['key_formatter']
                key_str = key_str.format(key)  # .replace(' ', '_')
                obj.save(key_str, hdf_args['oname'], path=hdf_args['path'])

            msg = 'case `{}` completed by {}'.format(key, this)
            tasks_that_are_done.put(msg)

    return True


class SimulationHandler(object):
    """Class handling parameter variations.

    Class adds methods to switch between multiple configurations.
    """

    def __init__(self,
                 defaults,
                 variation,
                 output,
                 oname,
                 verbosity=0,
                 path='.'):
        """Constructor"""

        # parse arguments
        self._defaults = defaults
        self._variation = variation
        self._output = output
        self.verbosity = verbosity

        # obtain parameter variation
        if len(self._variation) == 0:
            # no variation detected;
            self._variation_tuple = (None, None), None
        else:
            # buffer variation
            pvar, kvar = self._variation.get('entry', (None, None))
            values = self._variation.get('values', None)
            self._variation_tuple = (pvar, kvar), values

        vals = self._variation_tuple[1]
        if self.verbosity and vals is not None:
            print('Simulated values: {}'.format(vals))

        self.oname = oname
        self.path = path

        if self.oname is not None:

            # overwrite naming defaults from yaml (overrides)
            fileparts = oname.split('.')
            self._output['name'] = '.'.join(fileparts[:-1])
            self._output['format'] = fileparts[-1]

            if self._output['format'] in ['hdf', 'h5', 'hdf5', 'xlsx']:

                # save defaults to output file
                fname = (os.sep).join([self.path, self.oname])
                meta = pd.Series(flatten(self._defaults))
                var = pd.Series(flatten(self._variation))
                if self._output['format'] == 'xlsx':
                    with pd.ExcelWriter(
                            fname, engine='openpyxl', mode='w') as writer:
                        meta.to_excel(writer, sheet_name='defaults')
                    with pd.ExcelWriter(
                            fname, engine='openpyxl', mode='a') as writer:
                        var.to_excel(writer, sheet_name='variation')
                else:
                    meta.to_hdf(fname, 'defaults', mode='w')
                    var.to_hdf(fname, 'variation', mode='a')
            else:
                raise NotImplementedError(
                    'output as `.{}` is not implemented'.format(
                        output['format']))

    @classmethod
    def from_yaml(cls, yml_file, path='.', **kwargs):
        """Alternate constructor using YAML file as input.

        Args:
           yml_file (string): yaml file
        Kwargs:
           path (string): path to yaml file
           output (string): output name (overrides yaml)
           save_species (bool): flag (overrides yaml)
           kwargs (optional): dependent on implementation (e.g. verbosity, reacting)
        """
        # load configuration from yaml
        content = load_yaml(yml_file, path)
        output = content.get('output', {})

        # naming priorities: keyword / yaml / automatic
        name = kwargs.pop('name', None)
        if name is None:
            name = '.'.join(yml_file.split('.')[:-1])
            name = output.get('name', name)

        return cls.from_dict(content, name=name, **kwargs)

    @classmethod
    def from_dict(cls, content, **kwargs):
        """Alternate constructor using a dictionary as input.

        Args:
           content (dict): dictionary
        Kwargs:
           output (string): output name (overrides yaml)
           save_species (bool): flag (overrides yaml)
           kwargs (optional): dependent on implementation (e.g. verbosity, reacting)
        """

        assert 'version' in content, 'obsolete yaml file format'
        defaults = content.get('defaults', {})
        variation = content.get('variation', {})
        output = content.get('output', {})

        # save species override
        save_species = kwargs.pop('save_species', None)
        if save_species in [True, False]:
            output['save_species'] = save_species

        # reacting override
        reacting = kwargs.pop('reacting', None)
        if reacting in [True, False]:
            defaults['chemistry']['reacting'] = reacting

        # naming priorities: keyword / yaml / no name
        name = output.get('name', None)
        name = kwargs.pop('name', name)
        if name is not None:
            fmt = output.get('format', 'h5')
            fmt = kwargs.pop('format', fmt)
            name = '.'.join([name, fmt])

        return cls(defaults, variation, output, name, **kwargs)

    def __getattr__(self, attr):
        """Access settings dictionary as attribute"""

        assert attr in self._defaults.keys(), 'invalid attribute'
        return self._defaults[attr]

    def __iter__(self):
        """Returns itself as iterator"""

        for key in self._variation_tuple[1]:
            yield key

    def __getitem__(self, val):
        return self.simulation(val)

    def simulation(self, val):
        """Return """

        if val is None:
            return self._defaults

        pkvar, vals = self._variation_tuple
        pvar, kvar = pkvar
        assert val in vals, 'invalid value'

        out = deepcopy(self._defaults)
        if isinstance(out[pvar][kvar], list):
            out[pvar][kvar][0] = val
        else:
            out[pvar][kvar] = val

        out['verbosity'] = self.verbosity
        out['output'] = self._output

        return out

    @property
    def verbose(self):
        return self.verbosity > 0

    @property
    def variation(self):
        """Information on parameter variation"""
        return self._variation_tuple

    def keys(self):
        """keys of variation"""
        return self._variation_tuple[1]

    def item(self, key):
        """get item"""
        return key, self[key]

    def get_simulation(self, key, simulation=_Base):

        config = self[key]
        return simulation(**config)

    def run_serial(self, simulation=_Base, **kwargs):
        """Run variation in series"""

        for key in self.keys():

            # run simulation
            config = self[key]
            obj = simulation(**config)
            if self.verbosity > 0:
                pvar, kvar = self._variation_tuple[0]
                print(' * processing `{}.{}`: {}'.format(pvar, kvar, key))
            obj.initialize()
            obj.run()
            key_str = self._output.get('key_formatter', '{}')
            key_str = key_str.format(key)
            obj.save(key_str, self.oname, path=self.path)

        return True

    def run_parallel(self,
                     simulation=_Base,
                     number_of_processes=None,
                     **kwargs):
        """Run variation using multiprocessing"""

        tasks_to_accomplish = mp.Queue()
        finished_tasks = mp.Queue()

        if number_of_processes is None:
            number_of_processes = mp.cpu_count() // 2

        processes = []

        for k in self.keys():
            tasks_to_accomplish.put((k, self[k]))

        kwarg_dict = {
            'oname': self.oname,
            'path': self.path,
            'verbosity': self.verbosity,
            'key_formatter': self._output.get('key_formatter', '{}'),
        }

        lock = mp.Lock()

        # creating processes
        for w in range(number_of_processes):
            p = mp.Process(
                target=worker,
                args=(tasks_to_accomplish, finished_tasks, simulation, lock,
                      self._variation_tuple[0], kwarg_dict))
            processes.append(p)
            p.start()

        # completing process
        for p in processes:
            p.join()

        # print the output
        while not finished_tasks.empty():
            msg = finished_tasks.get()
            if self.verbosity > 1:
                print(msg)

        return True
