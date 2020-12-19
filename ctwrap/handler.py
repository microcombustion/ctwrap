"""The :mod:`handler` module defines a :class:`SimulationHandler` object
that handles batch jobs of wrapped :class:`Simulation` runs.

Simulation modules are passed to this module, where they are run in batches.
see `adiabatic flame example <adiabatic_flame_example.ipynb>`_ or
`ignition_example <ignition_example.ipynb>`_.

Class Definition
++++++++++++++++
"""

from pathlib import Path
from ruamel import yaml
import warnings

from typing import Dict, Any, Optional, Union

# multiprocessing
import multiprocessing as mp
import queue  # imported for using queue.Empty exception

# ctwrap specific import
from .parser import _parse, _write, Parser
from .strategy import Strategy, Sequence, Matrix
from .wrapper import Simulation


supported = ('.h5', '.hdf', '.hdf5')
indent1 = ' * '
indent2 = '   - '

class SimulationHandler(object):
    """
    Class handling parameter variations.
    Class adds methods to switch between multiple configurations.

    .. note:: :class:`SimulationHandler` objects should be
        instantiated using the :meth:`from_yaml` method.

    An example of a minimal yaml configuration is:

    .. code-block:: YAML

        strategy: # variation data
          sequence:
            sleep: [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
        defaults: # default parameters to run the modules
          sleep: 0.2

    If a :class:`simulationHandler` object was created from ``test_module.yaml``.
    To run a single task using :meth:`run_task` method or batch simulations
    in series :meth:`run_serial` method or parallel :meth:`run_parallel` method
    using a simulation object created using simulation module ``test_module``,
    each run method calls the ``run`` method in
    simulation module ``test_module``, saves the resulting output using
    the ``save``  method in simulation module ``test_module`` and also
    saves the `metatada`.

    Attributes:
       verbosity (int): verbosity level

    Arguments:
       strategy: Batch simulation strategy
       defaults: Dictionary containing simulation defaults
       output: Dictionary specifying file output
       verbosity: Verbosity level
    """

    def __init__(self,
                 strategy: Optional[Strategy]=None,
                 defaults: Dict[str, Any]=None,
                 output: Optional[Dict[str, Any]]=None,
                 verbosity: Optional[int]=0):
        """Constructor for `SimulationHandler` object."""

        # parse arguments
        self._strategy = strategy
        self._defaults = defaults
        self._output = output
        self.verbosity = verbosity

        self._tasks = self._strategy.create_tasks(self._defaults)
        if self.verbosity:
            print(self._strategy.info)

    @property
    def metadata(self):

        return {
            'defaults': self._defaults,
            'strategy': {self._strategy.name: self._strategy.definition},
            'tasks': list(self._tasks.keys())
        }

    @classmethod
    def from_yaml(cls, yaml_file: str,
                  strategy: Optional[str]=None,
                  name: Optional[str]=None,
                  path: Optional[str]=None,
                  **kwargs: str):
        """
        Alternate constructor using YAML file as input.

        The :meth:`from_yaml` method is intended as the main route for the creation of
        `SimulationHandler` objects.

        For example, a :class:`SimulationHandler` object can be created from a configuration file
        `test_module.yaml` to run a strategy `sequence` as shown below.

        .. code-block:: Python

           sh = ctwrap.SimulationHandler.from_yaml('test_module.yaml', strategy='sequence')

        Arguments:
           yaml_file: YAML file
           strategy: Batch job strategy name (only needed if more than one are defined)
           name: Output name (overrides yaml)
           path: File path (both yaml and output)
           **kwargs: Dependent on implementation (e.g. verbosity, reacting)
        """

        # load configuration from yaml
        fname = Path(yaml_file)
        if path is not None:
            fname = Path(path) / fname

        with open(fname) as stream:
            content = yaml.load(stream, Loader=yaml.SafeLoader)

        output = content.get('output', {})

        # naming priorities: keyword / yaml / automatic
        if name is None:
            name = '{}'.format(Path(yaml_file).parents[0] / fname.stem)
            name = output.get('name', name)

        return cls.from_dict(content, strategy=strategy, name=name, path=path, **kwargs)

    @classmethod
    def from_dict(cls, content: Dict[str, Any],
                  strategy: Optional[str]=None,
                  name: Optional[str]=None,
                  path: Optional[str]=None,
                  **kwargs: str) -> \
            Union['SimulationHandler', Dict[str, Any], str]:
        """
        Alternate constructor using a dictionary as input.

        Arguments:
           content: Dictionary from YAML input
           strategy: Batch job strategy name (only needed if more than one are defined)
           name: Output name (overrides yaml)
           path: Output path (overrides yaml)
           **kwargs: Dependent on implementation (e.g. verbosity, reacting)
        """
        assert 'ctwrap' in content, 'obsolete yaml file format'
        assert 'defaults' in content, 'obsolete yaml file format'

        if 'variation' in content and isinstance(content['variation'], dict):
            strategy = Sequence.from_legacy(content['variation'])
            warnings.warn("Old implementation", PendingDeprecationWarning)
        elif 'strategy' in content and isinstance(content['strategy'], dict):
            strategy = Strategy.load(content['strategy'], name=strategy)
        else:
            raise ValueError("Missing or invalid argument: need 'strategy' or 'variation' entry in dictionary")

        defaults = content['defaults']

        output = content.get('output', None)
        output = cls._parse_output(output, fname=name, fpath=path)

        return cls(strategy=strategy, defaults=defaults, output=output, **kwargs)

    @staticmethod
    def _parse_output(dct: Dict[str, Any],
                      fname: Optional[str] = None,
                      fpath: Optional[str] = None):
        """
        Parse output dictionary (hidden function)
        Overrides defaults with keyword arguments.

        Arguments:
           dct (dict, optional): dictionary from yaml input
           fname (name, optional): filename (overrides yaml)
           fpath (string, optional): output path (overrides yaml)

        Returns:
            Dictionary containing output information
        """

        if dct is None:
            return None

        # establish defaults
        out = dct.copy()
        out['path'] = None  # should never be specified inside of yaml
        if 'format' not in out:
            out['format'] = ''
        if 'force_overwrite' not in out:
            out['force_overwrite'] = False

        fformat = out['format']

        # file name keyword overrides dictionary
        if fname is not None:

            # fname may contain path information
            head = Path(fname).parent
            fname = Path(fname).name
            if str(head) != "." and fpath is not None:
                raise RuntimeError('contradictory specification')
            elif str(head) != ".":
                fpath = head

            fname = Path(fname).stem
            ext = Path(fname).suffix
            if ext in supported:
                fformat = ext

            out['name'] = fname

        # file path keyword overrides dictionary
        if fpath is not None:
            out['path'] = fpath

        # file format
        if fformat is None:
            pass
        elif len(fformat):
            out['format'] = fformat.lstrip('.')
        else:
            out['format'] = 'h5'

        if fformat is None:
            out['file_name'] = None
        else:
            out['file_name'] = '.'.join([out['name'], out['format']])

        return out

    def __iter__(self):
        """Returns itself as iterator"""

        for task in self._tasks:
            yield task

    def __getitem__(self, task: str):
        return self.configuration(task)

    def configuration(self, task: str):
        """
        Return configuration.

        Arguments:
           task: Task to do

        Returns:
           updated configuration dictionary based on the task
        """
        return self._tasks[task]

    @property
    def verbose(self):
        """verbosity"""
        return self.verbosity > 0

    @property
    def output_name(self):
        """return output name"""
        if self._output['path'] is None:
            return self._output['file_name']
        else:
            return Path(self._output['path']) / self._output['file_name']

    @property
    def tasks(self):
        """tasks defined in terms of the variation entry and values"""
        return self._tasks

    def run_task(self, sim: Simulation, task: str, **kwargs: str):
        """
        Function to run a specific task.

        The :meth:`run_task` method calls the module's run and save method to run and
        save the resulting output object and also afterwards calls
        :py:func:`~ctwrap.parser._save_metadata` to save metadata.
        A simple usage example is:

        .. code-block:: Python

            # Runs the task `sleep_0.4` using `sim` object
            sh.run_task(sim, 'sleep_0.4' )

        Arguments:
            sim (object): instance of Simulation class
            task (str): task to do
            ** kwargs (optional): dependent on implementation
            (e.g. verbosity, reacting)
        """

        assert task in self._tasks, 'unknown task `{}`'.format(task)

        # create a new simulation object
        obj = Simulation.from_module(sim._module, self._output)

        # run simulation
        config = self.configuration(task)

        group = "output_00"
        obj.run(group, config, **kwargs)
        obj._save(task=task)
        if self._output is not None:
            obj._save_metadata(self._output, self.metadata)

    def run_serial(self,
                   sim: Simulation,
                   verbosity: Optional[int] = None,
                   **kwargs: str) -> bool:
        """
        Run variation in series.

        The :meth:`run_serial` method runs all the strategy entries in the input
        file in serial and also saves metadata. A simple usage example is:

        .. code-block:: Python

            # Runs all the variations serially
            sh.run_serial(sim)

        Arguments:
            sim (object): instance of Simulation class
            verbosity (int, optional): verbosity
            ** kwargs (optional): dependent on implementation (e.g. verbosity, reacting)

        Returns:
            return True when task is completed
        """

        assert isinstance(sim, Simulation), 'need simulation object'

        if verbosity is None:
            verbosity = self.verbosity

        # create a new simulation object
        obj = Simulation.from_module(sim._module, self._output)

        tasks = list(self._tasks.keys())
        tasks.sort()
        for i, t in enumerate(tasks):
            if verbosity > 0:
                print(indent1 + 'processing `{}`'.format(t))

            # run simulation
            config = self.configuration(t)
            group = "output_{:0>2d}".format(i)
            obj.run(group, config, **kwargs)
            obj._save(task=t)
        if self._output is not None:
            obj._save_metadata(self._output, self.metadata)
        return True

    def run_parallel(self,
                     sim: Simulation,
                     number_of_processes: Optional[int] = None,
                     verbosity: Optional[str] = None,
                     **kwargs: str) -> bool:
        """
        Run variation using multiprocessing.

        The :meth:`run_parallel` method runs all the strategy entries in the input
        file in parallel using
        `python multiprocessing <https://docs.python.org/3/library/multiprocessing.html>`_.
        and also saves metadata.
        A simple usage is:

        .. code-block:: Python

            # Runs all the variations in parallel
            sh.run_parallel(sim)

        Arguments:
            sim (object): instance of Simulation class
            number_of_processes(int, optional): number of processes
            verbosity(int, optional): verbosity level
            ** kwargs (optional): dependent on implementation (e.g. verbosity, reacting)

        Returns:
            return True when task is completed
        """

        assert isinstance(sim, Simulation), 'need simulation object'

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
        tasks = list(self._tasks.keys())
        tasks.sort()
        for i, t in enumerate(tasks):
            config = self.configuration(t)
            group = "output_{:0>2d}".format(i)
            tasks_to_accomplish.put((t, group, config, kwargs))

        lock = mp.Lock()

        # creating processes
        processes = []
        for _ in range(number_of_processes):
            p = mp.Process(
                target=worker,
                args=(tasks_to_accomplish, finished_tasks, sim._module, lock,
                      self._output, verbosity))
            processes.append(p)
            p.start()

        # completing process
        for p in processes:
            p.join()

        # print the output
        while not finished_tasks.empty():
            msg = finished_tasks.get()
            if verbosity > 1:
                print(indent2 + msg)

        if self._output is not None:
            if verbosity > 1:
                print(indent1 + "Appending metadata")
            sim._save_metadata(self._output, self.metadata)

        return True


def worker(tasks_to_accomplish, tasks_that_are_done, module: str, lock,
           output: Dict[str, Any],
           verbosity: int) -> True:
    """
    Worker function for the `:meth: `run_parallel` method.

    Arguments:
        tasks_to_accomplish (queue): multiprocessing queue of remaining task
        tasks_that_are_done (queue): multiprocessing queue of complted task
        module (str): name of handler to be run
        lock (lock): multiprocessing lock
        output (dict): dictionary containing output information
        metadata (dict): dictionary containing metadata
        verbosity (int): verbosity level

    Returns:
        True when tasks are completed

    """

    this = mp.current_process().name

    if verbosity > 1:
        print(indent2 + 'starting ' + this)

    while True:
        try:
            # retrieve next simulation task
            task, group, config, kwargs = tasks_to_accomplish.get_nowait()

        except queue.Empty:
            # no tasks left
            if verbosity > 1:
                print(indent2 + 'terminating ' + this)
            break

        else:
            obj = Simulation.from_module(module, output)
            # perform task
            msg = indent1 + 'processing `{}` ({})'
            if verbosity > 0:
                print(msg.format(task, this))
            obj.run(group, config, **kwargs)
            with lock:
                obj._save(task=task)
            msg = 'case `{}` completed by {}'.format(task, this)
            tasks_that_are_done.put(msg)

    return True
