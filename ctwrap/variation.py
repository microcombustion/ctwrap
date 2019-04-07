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
from .configuration import _ReactorBase


__all__ = ['Variation']


def worker(tasks_to_accomplish, tasks_that_are_done, reactor, lock, var0,
           hdf_args):

    verbosity = hdf_args.get('verbosity', False)
    this = mp.current_process().name

    # check compliance of target object
    for m in ['__init__', 'run', 'save']:
        msg = 'Target object is missing required method `{}`'
        assert hasattr(reactor, m), msg.format(m)

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
            obj = reactor(**config)
            if verbosity > 0:
                pvar, kvar = var0
                msg = ' * processing `{}.{}`: {} ({})'
                print(msg.format(pvar, kvar, key, this))
            obj.run()
            with lock:
                key_str = hdf_args['key_formatter']
                key_str = key_str.format(key)  # .replace(' ', '_')
                obj.save(key_str, hdf_args['oname'], path=hdf_args['path'])

            msg = 'case `{}` completed by {}'.format(key, this)
            tasks_that_are_done.put(msg)

    return True


class Variation(object):
    """Class handling parameter variations.

    Class adds methods to switch between multiple configurations.
    """

    def __init__(self,
                 configuration,
                 variation,
                 output,
                 oname,
                 verbosity=0,
                 path='.'):
        """Constructor"""

        # parse arguments
        self._configuration = configuration
        # self._configuration.update(kwargs)
        self._variation = variation
        self._output = output
        self.verbosity = verbosity

        self.oname = oname
        self.path = path

        # overwrite naming defaults from yaml (overrides)
        fileparts = oname.split('.')
        self._output['name'] = '.'.join(fileparts[:-1])
        self._output['format'] = fileparts[-1]

        #output = self._configuration['output']
        if self._output['format'] in ['hdf', 'h5', 'hdf5', 'xlsx']:

            # save configuration to output file
            fname = (os.sep).join([self.path, self.oname])
            meta = pd.Series(flatten(self._configuration))
            var = pd.Series(flatten(self._variation))
            if self._output['format'] == 'xlsx':
                with pd.ExcelWriter(
                        fname, engine='openpyxl', mode='w') as writer:
                    meta.to_excel(writer, sheet_name='configuration')
                with pd.ExcelWriter(
                        fname, engine='openpyxl', mode='a') as writer:
                    var.to_excel(writer, sheet_name='variation')
            else:
                meta.to_hdf(fname, 'configuration', mode='w')
                var.to_hdf(fname, 'variation', mode='a')
        else:
            raise (NotImplementedError,
                   'output as `.{}` is not implemented'.format(
                       output['format']))

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

    @classmethod
    def from_yaml(cls, yml_file, **kwargs):
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
        path = kwargs.get('path', '.')
        #fname = (os.sep).join([path, yml_file])
        content = load_yaml(yml_file, path)
        # with open(fname, 'r') as yml:
        #    content = parse_yaml(yml)
        assert 'version' in content, 'obsolete yaml file format'
        configuration = content.get('configuration', {})
        variation = content.get('variation', {})
        output = content.get('output', {})

        # naming priorities: keyword / yaml / automatic naming
        name = kwargs.pop('output', None)
        if name is None:
            oname = '.'.join(yml_file.split('.')[:-1])
            oname = output.get('name', oname)
            name = '{}.{}'.format(oname, output['format'])

        # save species override
        save_species = kwargs.pop('save_species', None)
        if save_species in [True, False]:
            output['save_species'] = save_species

        # reacting override
        reacting = kwargs.pop('reacting', None)
        if reacting in [True, False]:
            configuration['chemistry']['reacting'] = reacting

        return cls(configuration, variation, output, name, **kwargs)

    def __getattr__(self, attr):
        """Access settings dictionary as attribute"""

        assert attr in self._configuration.keys(), 'invalid attribute'
        return self._configuration[attr]

    def __iter__(self):
        """Returns itself as iterator"""

        for key in self._variation_tuple[1]:
            yield key

    def __getitem__(self, val):
        """Return """

        if val is None:
            return self._configuration

        pkvar, vals = self._variation_tuple
        pvar, kvar = pkvar
        assert val in vals, 'invalid value'

        out = deepcopy(self._configuration)
        if isinstance(out[pvar][kvar], list):
            out[pvar][kvar][0] = val
        else:
            out[pvar][kvar] = val

        fuel = out.pop('fuel', None)
        if fuel is not None:
            out['initial']['fuel'] = self.get_fuel(fuel)

        out['verbosity'] = self.verbosity
        out['output'] = self._output

        return out

    def get_fuel(self, fdict):

        fuel = fdict['name']
        blend = fdict.get('blend', None)
        if blend is None:
            fraction = 0.
            name = 'tbd'
        else:
            fraction = .01 * fdict['blend_percent'][0]
            name = fdict.get('blend_name',
                             '{}_{{}}'.format(blend)).format(fraction * 100)

        return self._get_fuel(fuel, blend, fraction, name)

    def _get_fuel(self, fuel, blend, fraction, name):

        assert fuel is not None, 'information on fuel is missing'

        if fuel in zdt.species_alias():
            fuel = zdt.NeatFuel.from_database(fuel)
        elif fuel in zdt.list_blends():
            fuel = zdt.BlendedFuel.from_recipe(fuel)
        else:
            raise ValueError('unknown entry for `fuel`')

        if blend is None:
            out = fuel
        else:
            if blend in zdt.species_alias():
                blend = zdt.NeatFuel.from_database(blend)
            elif blend in zdt.list_blends():
                blend = zdt.BlendedFuel.from_recipe(blend)
            out = zdt.BlendedFuel.mix(fuel, blend, fraction, name)

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

    def get_reactor(self, key, reactor=_ReactorBase):

        config = self[key]
        return reactor(**config)

    def run_serial(self, reactor=_ReactorBase, **kwargs):
        """Run variation in series"""

        for key in self.keys():

            # run reactor
            config = self[key]
            obj = reactor(**config)
            if self.verbosity > 0:
                pvar, kvar = self._variation_tuple[0]
                print(' * processing `{}.{}`: {}'.format(pvar, kvar, key))
            obj.run()
            key_str = self._output.get('key_formatter', '{}')
            key_str = key_str.format(key)  # .replace(' ', '_')
            obj.save(key_str, self.oname, path=self.path)

        return True

    def run_parallel(self,
                     reactor=_ReactorBase,
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
                args=(tasks_to_accomplish, finished_tasks, reactor, lock,
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
