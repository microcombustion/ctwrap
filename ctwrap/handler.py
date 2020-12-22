"""The :py:mod:`handler` module defines a :class:`SimulationHandler` object
that handles batch jobs of wrapped :any:`Simulation` module runs.

Usage
+++++

:class:`SimulationHandler` objects run batch jobs based on YAML configuration
files. A simple example for a YAML configuration is:

.. code-block:: YAML

   strategy: # parameter variation
     sequence-1:
       spam: [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]
     sequence-2:
       eggs: [1, 2, 3]
   defaults: # default parameters
     spam: 0.5
     eggs: 1
   output:
     format: h5

In the following, a :class:`SimulationHandler` object is used to run
batch simulations of a :class:`Simulation` module defined in ``my_test.py``,
where the ``run`` method takes two arguments (*spam* and *eggs*).
Assuming that the YAML configuration file ``my_test.yaml`` corresponds to the
YAML block above, the simulation strategy *sequence-2* is loaded by issuing

.. code-block:: Python

   import ctwrap as cw

   seq = cw.SimulationHandler('my_test.yaml', strategy='sequence-2')
   tasks = seq.tasks # dictionary with entries 'eggs_1', 'eggs_2', 'eggs_3'

Once loaded, tasks are passed to a :class:`Simulation` object wrapping ``my_test.py``:

.. code-block:: Python

   sim = cw.Simulation.from_module('my_test.py')

   seq.configuration('eggs_2) # return task configuration
   seq.run_task(sim, 'eggs_2') # run a single simulation task

   seq.run_serial(sim) # run all tasks in series
   seq.run_parallel(sim) # run all tasks as parallel processes

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
from .output import Output


indent1 = ' * '
indent2 = '   - '

class SimulationHandler(object):
    """
    Class handling parameter variations.
    Class adds methods to switch between multiple configurations.

    .. note:: :class:`SimulationHandler` objects should be instantiated
        using factory methods :meth:`from_yaml` or :meth:`from_dict`.

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
        self.verbosity = verbosity # type: int

        if output is not None:
            out = Output.from_dict(output)
            if out.force:
                dest = Path(out.output_name)
                if dest.is_file():
                    dest.unlink()
            output = out.settings

        self._output = output

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
        :class:`SimulationHandler` objects.

        Arguments:
           yaml_file: YAML file
           strategy: Batch job strategy name (only needed if more than one are defined)
           name: Output name (overrides yaml)
           path: File path (both yaml and output)
           **kwargs: Dependent on implementation
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
           **kwargs: Dependent on implementation
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
        if output is not None:
            output = Output.from_dict(output, file_name=name, file_path=path).settings

        return cls(strategy=strategy, defaults=defaults, output=output, **kwargs)

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
            return self._output['name']
        else:
            return Path(self._output['path']) / self._output['name']

    @property
    def tasks(self):
        """tasks defined in terms of the variation entry and values"""
        return self._tasks

    def run_task(self, sim: Simulation, task: str, **kwargs: str):
        """
        Function to run a specific task.

        The :meth:`run_task` method calls the module's run method and
        saves the resulting output and metadata. A simple example is:

        .. code-block:: Python

            # Runs the task `sleep_0.4` using `sim` object
            sh.run_task(sim, 'sleep_0.4' )

        Arguments:
           sim: instance of :class:`Simulation` class
           task: task to do
           **kwargs: dependent on implementation
        """

        assert task in self._tasks, 'unknown task `{}`'.format(task)

        # create a new simulation object
        obj = Simulation.from_module(sim._module, self._output)

        # get configuration
        config = obj.defaults()
        overload = self.configuration(task)
        config.update(overload)

        # run simulation
        group = "task_0"
        obj.run(group, config, **kwargs)
        obj._save(task=task)
        if self._output is not None:
            out = Output.from_dict(self._output)
            out.save_metadata(self.metadata)

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
            sim: instance of :class:`Simulation` class
            verbosity: verbosity
            **kwargs: dependent on implementation

        Returns:
            True when task is completed
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

            # get configuration
            config = obj.defaults()
            overload = self.configuration(t)
            config.update(overload)

            # run simulation
            group = "task_{:d}".format(i)
            obj.run(group, config, **kwargs)
            obj._save(task=t)
        if self._output is not None:
            out = Output.from_dict(self._output)
            out.save_metadata(self.metadata)
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

        .. code-block:: Python

            # Runs all the variations in parallel
            sh.run_parallel(sim) # run

        Arguments:
            sim: instance of Simulation class
            number_of_processes: number of processes
            verbosity: verbosity level
            **kwargs: dependent on implementation

        Returns:
            True when task is completed
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
            overload = self.configuration(t)
            group = "task_{:d}".format(i)
            tasks_to_accomplish.put((t, group, overload, kwargs))

        lock = mp.Lock()

        # creating processes
        processes = []
        for _ in range(number_of_processes):
            p = mp.Process(
                target=_worker,
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
            out = Output.from_dict(self._output)
            out.save_metadata(self.metadata)

        return True


def _worker(tasks_to_accomplish, tasks_that_are_done, module: str, lock,
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
            task, group, overload, kwargs = tasks_to_accomplish.get_nowait()

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

            config = obj.defaults()
            config.update(overload)
            obj.run(group, config, **kwargs)
            with lock:
                obj._save(task=task)
            msg = 'case `{}` completed by {}'.format(task, this)
            tasks_that_are_done.put(msg)

    return True
