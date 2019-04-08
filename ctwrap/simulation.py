#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Object handling variations."""

from copy import deepcopy
import warnings

# multiprocessing
import multiprocessing as mp
import queue  # imported for using queue.Empty exception

# ctwrap specific imports
from . import fileio
from .parsers import parse_output

__all__ = ['SimulationHandler']

indent1 = ' * '
indent2 = '   - '


class _PluginHandler(object):
    """Rudimentary functions required by a simulation object"""

    def __init__(self, func_handle, output, verbosity=0):
        """Base plugin constructor

        Arguments:
           fcn_handle (function): function that runs the simulation
           output (dict): description of file output

        Keyword Arguments:
           verbosity (int): verbosity level
        """

        self.func_handle = func_handle
        self.verbosity = verbosity
        self._output = output

    def dispatch(self, name, config, verbosity=None, **kwargs):
        """Dispatch function holding configuration in dictionary.

        Args:
           func_handle (function): function that runs the simulation
           config (dict): configuration
        Kwargs:
           kwargs (optional): depends on implementation of __init__

        dispatch_from_yaml does not support an output formatter.
        """

        if verbosity is not None:
            self.verbosity = verbosity

        name_ = self._output['task_formatter'].format(name)
        self.data = self.func_handle(
            name_, **config, **kwargs, verbosity=self.verbosity)

    # def dispatch_from_yaml(self,
    #                        name,
    #                        yaml_file,
    #                        path='.',
    #                        verbosity=None,
    #                        **kwargs):
    #     """Alternate dispatch function using YAML file as input.

    #     Args:
    #        func_handle (function): function that runs the simulation
    #        yaml_file (string): yaml file
    #     Kwargs:
    #        path (string): path to yaml file
    #        kwargs (optional): depends on implementation of __init__

    #     dispatch_from_yaml does not support an output formatter.
    #     """

    #     # load configuration from yaml
    #     content = fileio.load_yaml(yml_file, path)
    #     config = content.get('configuration', {})

    #     if verbosity is not None:
    #         self.verbosity = verbosity

    #     name_ = self._output['task_formatter'].format(name)
    #     self.data = self.func_handle(
    #         name_, **config, **kwargs, verbosity=self.verbosity)

    # @property
    # def verbose(self):
    #     """Verbosity level"""
    #     return self.verbosity > 0

    def save(self):
        """save simulation data"""

        if self._output is None:
            return

        oname = self._output['file_name']
        opath = self._output['path']
        force = self._output['force_overwrite']

        fileio.save(oname, self.data, mode='a', force=force, path=opath)


class SimulationHandler(object):
    """Class handling parameter variations.

    Class adds methods to switch between multiple configurations.
    """

    def __init__(self,
                 configuration,
                 variation,
                 output,
                 plugin=None,
                 verbosity=0,
                 path='.'):
        """Constructor"""

        # parse arguments
        self._configuration = configuration
        self._variation = variation
        self._output = output
        self.plugin = plugin
        self.verbosity = verbosity

        # obtain parameter variation
        if self._variation is None:
            # no variation detected;
            self._entry = None
            self._tasks = None
        else:
            # buffer variation
            var = self._variation

            # transition
            if 'values' in var:
                warnings.warn(
                    'YAML key `variation.values` is superseded '
                    'by `variation.tasks`', PendingDeprecationWarning)
                if 'tasks' not in var:
                    var['tasks'] = var['values']

            # transition
            if 'entry' in var:
                warnings.warn(
                    'YAML key `variation.entry` is superseded '
                    'by `variation.configuration_entry`',
                    PendingDeprecationWarning)
                if 'tasks' not in var:
                    var['configuraton_entry'] = var['entry']

            msg = 'missing entry `{}` in `variation`'
            for key in ['configuration_entry', 'tasks']:
                assert key in var, msg.format(key)

            self._entry = var['configuration_entry']
            self._tasks = var['tasks']

        # vals = self._variation_tuple[1]
        if self.verbosity and self._tasks is not None:
            print('Simulation tasks: {}'.format(self._tasks))

        if self._output is not None:

            # assemble information
            info = {
                'configuration': self._configuration,
                'variation': self._variation
            }

            # save to file
            oname = self._output['file_name']
            path = self._output['path']
            force = self._output['force_overwrite']

            fileio.save(oname, info, mode='w', force=force, path=path)

    @classmethod
    def from_yaml(cls,
                  yml_file,
                  yml_path=None,
                  oname=None,
                  opath=None,
                  **kwargs):
        """Alternate constructor using YAML file as input.

        Args:
           yml_file (string): yaml file
        Kwargs:
           yml_path (string): path to yaml file
           oname (string): output name (overrides yaml)
           opath (string): output path (overrides yaml)
           kwargs (optional): dependent on implementation (e.g. verbosity, reacting)
        """
        # load configuration from yaml
        content = fileio.load_yaml(yml_file, yml_path)
        output = content.get('output', {})

        # naming priorities: keyword / yaml / automatic
        if oname is None:
            oname = '.'.join(yml_file.split('.')[:-1])
            oname = output.get('name', oname)

        return cls.from_dict(content, oname=oname, opath=opath, **kwargs)

    @classmethod
    def from_dict(cls, content, oname=None, opath=None, **kwargs):
        """Alternate constructor using a dictionary as input.

        Args:
           content (dict): dictionary
        Kwargs:
           oname (string): output name (overrides yaml)
           opath (string): output path (overrides yaml)
           kwargs (optional): dependent on implementation (e.g. verbosity, reacting)
        """

        assert 'ctwrap' in content, 'obsolete yaml file format'
        configuration = content.get('configuration', {})
        variation = content.get('variation', None)
        output = content.get('output', None)

        output = parse_output(output, fname=oname, fpath=opath)

        return cls(configuration, variation, output, **kwargs)

    def __iter__(self):
        """Returns itself as iterator"""

        for task in self._tasks:
            yield task

    def __getitem__(self, task):
        return self.configuration(task)

    def configuration(self, task=None, verbosity=None):
        """Return """

        if verbosity is None:
            verbosity = self.verbosity

        if task is None:
            return self._configuration
        else:
            assert task in self._tasks, 'invalid value'
            out = deepcopy(self._configuration)

        # locate entry in nested dictionary (recursive)
        def replace_entry(nested, key_list, value):
            sub = nested[key_list[0]]
            if len(key_list) == 1:
                if isinstance(sub, list):
                    sub[0] = value
                else:
                    sub = value
            else:
                sub = replace_entry(sub, key_list[1:], value)
            nested[key_list[0]] = sub
            return nested

        entry = replace_entry(out, self._entry, task)

        # out['verbosity'] = verbosity

        return out

    @property
    def verbose(self):
        return self.verbosity > 0

    @property
    def oname(self):
        if self._output['path'] is None:
            return self._output['file_name']
        else:
            return self._output['path'] + self._output['file_name']

    @property
    def tasks(self):
        """values of variation"""
        return self._tasks

    def dispatch(self, task, plugin=None, verbosity=None, **kwargs):

        assert callable(plugin), 'plugin needs to be a function'

        if verbosity is None:
            verbosity = self.verbosity

        obj = _PluginHandler(plugin, self._output, verbosity)

        # run simulation
        config = self.configuration(task)

        obj.dispatch(task, config, verbosity=verbosity, **kwargs)
        obj.save()

    def run_serial(self, plugin=None, verbosity=None, **kwargs):
        """Run variation in series"""

        assert callable(plugin), 'plugin needs to be a function'

        if verbosity is None:
            verbosity = self.verbosity

        obj = _PluginHandler(plugin, self._output, verbosity)

        for task in self._tasks:

            if verbosity > 0:
                entry = '.'.join(self._entry)
                print(indent1 + 'processing `{}`: {}'.format(entry, task))

            # run simulation
            config = self.configuration(task)

            obj.dispatch(task, config, verbosity=verbosity, **kwargs)
            obj.save()

        return True

    def run_parallel(self,
                     plugin=None,
                     number_of_processes=None,
                     verbosity=None,
                     **kwargs):
        """Run variation using multiprocessing"""

        assert callable(plugin), 'plugin needs to be a function'

        if number_of_processes is None:
            number_of_processes = mp.cpu_count() // 2

        if verbosity is None:
            verbosity = self.verbosity

        if verbosity > 0:
            print(indent1 + 'running simulation using ' +
                  '{} cores'.format(number_of_processes))

        # set up queues
        tasks_to_accomplish = mp.Queue()
        finished_tasks = mp.Queue()
        for t in self._tasks:
            config = self.configuration(t, verbosity)
            tasks_to_accomplish.put((t, config, kwargs))

        lock = mp.Lock()

        entry = '.'.join(self._entry)
        msg = indent1 + \
            'processing `{}`: {{}} ({{}})'.format('.'.join(self._entry))

        # creating processes
        processes = []
        for w in range(number_of_processes):
            p = mp.Process(
                target=worker,
                args=(tasks_to_accomplish, finished_tasks, plugin, lock, msg,
                      self._output, verbosity))
            processes.append(p)
            p.start()

        # completing process
        for p in processes:
            p.join()

        # print the output
        if verbosity > 0:
            print('=' * 60)
            print('Summary:')
        while not finished_tasks.empty():
            msg = finished_tasks.get()
            if verbosity > 0:
                print(indent1 + msg)

        return True


def worker(tasks_to_accomplish, tasks_that_are_done, plugin, lock, msg, output,
           verbosity):

    this = mp.current_process().name

    if verbosity > 0:
        print(indent1 + 'starting ' + this)

    while True:
        try:
            # retrieve next simulation task
            task, config, kwargs = tasks_to_accomplish.get_nowait()

        except queue.Empty:
            # no tasks left
            if verbosity > 0:
                print(indent1 + 'terminating ' + this)
            break

        else:

            obj = _PluginHandler(plugin, output, verbosity)

            # perform task
            if verbosity > 0:
                print(msg.format(task, this))
            obj.dispatch(task, config, verbosity=verbosity, **kwargs)
            with lock:
                obj.save()

            msg = 'case `{}` completed by {}'.format(task, this)
            tasks_that_are_done.put(msg)

    return True
