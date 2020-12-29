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
import textwrap

from typing import Dict, Any, Optional, Union

# multiprocessing
import multiprocessing as mp
from multiprocessing import queues as mpq
from multiprocessing import synchronize as mps
import queue  # imported for using queue.Empty exception

# ctwrap specific import
from .parser import _parse, _write, Parser
from .strategy import Strategy, Sequence, Legacy, Matrix
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

        self._variations = self._strategy.variations
        self._configurations = self._strategy.configurations(self._defaults)
        if self.verbosity:
            msg = textwrap.wrap(self._strategy.info, 80)
            print('\n'.join(msg))

    @property
    def metadata(self):

        return {
            'defaults': self._defaults,
            'strategy': self._strategy.definition,
            'cases': self._variations
        }

    @classmethod
    def from_yaml(cls, yaml_file: str,
                  strategy: Optional[str]=None,
                  output_name: Optional[str]=None,
                  database: Optional[str]=None,
                  **kwargs: Optional[Dict]):
        """
        Alternate constructor using YAML file as input.

        The :meth:`from_yaml` method is intended as the main route for the creation of
        :class:`SimulationHandler` objects.

        Arguments:
           yaml_file: YAML file
           strategy: Batch job strategy name (only needed if more than one are defined)
           output_name: Output name (overrides YAML configuration)
           database: File database (both YAML configuration and output)
           **kwargs: Dependent on implementation
        """

        if 'path' in kwargs:
            database = kwargs.pop['path'] # pylint: disable=unsubscriptable-object
            warnings.warn("Parameter 'path' is superseded by 'database'", DeprecationWarning)

        # load configuration from yaml
        fname = Path(yaml_file)
        if database is not None:
            fname = Path(database) / fname

        with open(fname) as stream:
            content = yaml.load(stream, Loader=yaml.SafeLoader)

        output = content.get('output', {})

        # naming priorities: keyword / yaml / automatic
        if output_name is None:
            name = '{}'.format(Path(yaml_file).parents[0] / fname.stem)
            name = output.get('name', name)

        return cls.from_dict(content, strategy=strategy, output_name=name, output_path=database, **kwargs)

    @classmethod
    def from_dict(cls, content: Dict[str, Any],
                  strategy: Optional[str]=None,
                  output_name: Optional[str]=None,
                  output_path: Optional[str]=None,
                  **kwargs: Optional[Dict]
        ) -> Union['SimulationHandler', Dict[str, Any], str]:
        """
        Alternate constructor using a dictionary as input.

        Arguments:
           content: Dictionary from YAML input
           strategy: Batch job strategy name (only needed if more than one are defined)
           output_name: Output name (overrides YAML configuration)
           output_path: Output path (overrides YAML configuration)
           **kwargs: Dependent on implementation
        """
        assert 'ctwrap' in content, 'obsolete yaml file format'
        assert 'defaults' in content, 'obsolete yaml file format'

        if 'name' in kwargs:
            output_name = kwargs.pop['name'] # pylint: disable=unsubscriptable-object
            warnings.warn("Parameter 'name' is superseded by 'output_name'", DeprecationWarning)
        if 'path' in kwargs:
            output_path = kwargs.pop['path'] # pylint: disable=unsubscriptable-object
            warnings.warn("Parameter 'path' is superseded by 'output_path'", DeprecationWarning)

        if 'variation' in content and isinstance(content['variation'], dict):
            strategies = Legacy.convert(content['variation'])
            strategy = None
            warnings.warn("Old implementation", PendingDeprecationWarning)
        elif 'strategy' in content and isinstance(content['strategy'], dict):
            strategies = content['strategy']
        else:
            raise ValueError("Missing or invalid argument: need 'strategy' or 'variation' entry in dictionary")

        strategy = Strategy.load(strategies, name=strategy)
        defaults = content['defaults']

        output = content.get('output', None)
        if output is not None:
            output = Output.from_dict(output, file_name=output_name, file_path=output_path).settings

        return cls(strategy=strategy, defaults=defaults, output=output, **kwargs)

    def __iter__(self):
        """Returns itself as iterator"""

        for task in self._variations:
            yield task

    def __getitem__(self, task: str):
        return self._variations(task)

    def configuration(self, task: str):
        """
        Return configuration.

        Arguments:
           task: Task to do

        Returns:
           updated configuration dictionary based on the task
        """
        return self._configurations[task]

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
        return self._variations

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
        # pylint: disable=no-member

        assert task in self._variations, 'unknown task `{}`'.format(task)

        if kwargs:
            warnings.warn("Keyword arguments are deprecated and ignored", DeprecationWarning)

        # create a new simulation object
        obj = Simulation.from_module(sim._module)

        # get configuration
        config = obj.defaults()
        overload = self.configuration(task)
        config.update(overload)

        # run simulation
        obj.run(config)
        if self._output and obj.data:
            out = Output.from_dict(self._output)
            out.save(obj.data, entry=task, variation=self._variations[task])
            out.finalize(self.metadata)

    def _setup_batch(self, parallel: bool=False):
        """Create batch queues used by worker function"""

        if parallel:
            tasks_to_accomplish = mp.Queue()
        else:
            tasks_to_accomplish = queue.Queue()
        for task, overload in self._configurations.items():
            tasks_to_accomplish.put((task, overload))

        return tasks_to_accomplish

    def run_serial(self,
                   sim: Simulation,
                   verbosity: Optional[int]=None,
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

        if kwargs:
            warnings.warn("Keyword arguments are deprecated and ignored", DeprecationWarning)

        if verbosity is None:
            verbosity = self.verbosity

        if verbosity > 0:
            print(indent1 + 'Starting serial batch simulation')

        # set up queues and dispatch worker
        tasks_to_accomplish = self._setup_batch(parallel=False)
        lock = None
        _worker(sim._module, self._strategy.definition, self._output,
                tasks_to_accomplish, lock, verbosity)

        if self._output is not None:
            out = Output.from_dict(self._output)
            out.finalize(self.metadata)
        return True

    def run_parallel(self,
                     sim: Simulation,
                     number_of_processes: Optional[int]=None,
                     verbosity: Optional[int]=None,
                     **kwargs: Optional[Any]) -> bool:
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

        if kwargs:
            warnings.warn("Keyword arguments are deprecated and ignored", DeprecationWarning)

        if number_of_processes is None:
            number_of_processes = mp.cpu_count() // 2

        if verbosity is None:
            verbosity = self.verbosity

        if verbosity > 0:
            print(indent1 + 'Starting parallel batch simulation using ' +
                  '{} cores'.format(number_of_processes))

        # set up queues and lock
        tasks_to_accomplish = self._setup_batch(parallel=True)
        lock = mp.Lock()

        # creating processes
        processes = []
        for _ in range(number_of_processes):
            p = mp.Process(
                target=_worker,
                args=(sim._module, self._strategy.definition, self._output,
                      tasks_to_accomplish, lock, verbosity))
            p.start()
            processes.append(p)

        # completing process
        for p in processes:
            p.join()

        if self._output is not None:
            if verbosity > 1:
                print(indent1 + "Appending metadata")
            out = Output.from_dict(self._output)
            out.finalize(self.metadata)

        return True


def _worker(
        module: str,
        strategy: Dict[str, Any],
        output: Dict[str, Any],
        tasks_to_accomplish: mpq.Queue,
        lock: mps.Lock,
        verbosity: int
    ) -> True:
    """
    Worker function running simulation queues.

    Arguments:
        module: Name of simulation module to be run
        tasks_to_accomplish: Queue of remaining tasks
        lock: Multiprocessing lock (used for parallel simulations only)
        output: Dictionary containing output information
        verbosity: Verbosity level

    Returns:
        True when tasks are completed
    """
    # pylint: disable=no-member

    parallel = isinstance(lock, mp.synchronize.Lock)
    if parallel:
        this = mp.current_process().name
    else:
        this = 'main'

    if verbosity > 1 and parallel:
        print(indent2 + 'starting ' + this)

    # create local copy of strategy object
    strategy = Strategy.load(strategy)
    variations = strategy.variations # pylint: disable=no-member
    tasks = set(variations.keys())

    # create local copy of output object
    if isinstance(output, dict):
        out = Output.from_dict(output)
    else:
        out = None

    other = None
    reschedule = 0
    while reschedule < len(tasks):
        try:
            # retrieve next simulation task
            task, overload = tasks_to_accomplish.get_nowait()

        except queue.Empty:
            # no tasks left
            if verbosity > 1 and parallel:
                print(indent2 + 'terminating ' + this)
            break

        try:
            # create object
            obj = Simulation.from_module(module)

            base = strategy.base(task)
            restart = None
            if obj.has_restart and out and base:
                if parallel:
                    with lock:
                        done = set(out.dir())
                        restart = out.load_like(base, other)
                else:
                    done = set(out.dir())
                    restart = out.load_like(base, other)
                invalid = done - tasks # empty if labels follow task names
                if restart is None and not invalid:
                    # need to pick another task
                    if verbosity > 1:
                        print(indent2 + 'rescheduling {} ({})'.format(task, this))
                    tasks_to_accomplish.put((task, overload))
                    reschedule += 1
                    continue

            if verbosity > 0:
                msg = indent1 + 'running `{}` ({})'
                print(msg.format(task, this))

            # run task
            config = obj.defaults()
            config.update(overload)

            if restart is None:
                obj.run(config)
            else:
                obj.restart(restart, config)

            data = obj.data
            errored = False

        except Exception as err:
            # Convert exception to warning
            msg = "Simulation of '{}' for '{}' failed with error message:\n{}".format(type(obj).__name__, task, err)
            warnings.warn(msg, RuntimeWarning)

            data = {task: (type(err).__name__, str(err))}
            errored = True

        # save output
        if out and obj.data:
            if parallel:
                with lock:
                    out.save(data, entry=task, variation=variations[task], errored=errored)
            else:
                out.save(data, entry=task, variation=variations[task], errored=errored)

            other = obj.data

    return True
