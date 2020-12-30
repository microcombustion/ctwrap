"""The :py:mod:`wrapper` module defines a :class:`Simulation` object that
wraps simulation modules.

Usage
+++++

Simulation modules specify tasks to be run in a batch job; a simulation
module needs to define methods ``defaults`` (default parameters) and
``run`` (running of batch calculations).

:py:mod:`ctwrap` defines several pre-configured simulation modules in the
:py:mod:`ctwrap.modules` submodule. As an example, the :py:mod:`ctwrap.modules.minimal`
module is loaded using the module path as:

.. code-block:: Python

   import ctwrap as cw

   sim = cw.Simulation.from_module('ctwrap.modules.minimal')
   sim = cw.Simulation.from_module(cw.modules.minimal) # equivalent

Alternatively, a :class:`Simulation` module defined in ``my_test.py``
is loaded as:

.. code-block:: Python

   sim = cw.Simulation.from_module('my_test.py')

Methods defined within a simulation module can be accessed by
pass-through methods :meth:`Simulation.defaults` and :meth:`Simulation.new`:

.. code-block:: Python

   defaults = sim.defaults() # load defaults
   sim.run(defaults) # run simulation module with default arguments

Class Definition
++++++++++++++++
"""
from pathlib import Path
import importlib
import warnings

from typing import Dict, Any, Optional, Union


# ctwrap specific import
from .parser import Parser


class Simulation(object):
    """
    The Simulation class wraps simulation modules into a callable object.

    .. note:: :class:`Simulation` objects should be instantiated using
        the :meth:`from_module` method.

    Attributes:
        data: Dictionary containing simulation results.

    Arguments:
        module: Handle name or handle to module running the simulation
    """

    def __init__(self, module: str):
        """Constructor for `Simulation` object."""

        assert isinstance(module, str), 'need module name'

        self._module = module
        self.data = None # type: Dict

        # ensure that module is well formed
        mod = self._load_module()
        msg = 'module `{}` is missing attribute `{}`'
        for attr in ['defaults', 'run']:
            assert hasattr(mod, attr), msg.format(module, attr)

        if hasattr(mod, 'save'):
            warnings.warn("Method 'save' in simulation modules are ignored",
                          DeprecationWarning)

        self.has_restart = hasattr(mod, 'restart')

    @classmethod
    def from_module(cls, module: str) -> 'Simulation':
        """
        Alternative constructor for `Simulation` object.

        The :meth:`from_module` method is intended as the main route for the creation of
        `Simulation` objects. For example:

        .. code-block:: Python

           # creates a simulation object with the simulation module `minimal`
           sim = ctwrap.Simulation.from_module(ctwrap.modules.minimal)

        Arguments:
           module (module): handle name or handle to module running the simulation
        """

        # create a name that reflect the module name (CamelCase)
        if isinstance(module, (str, Path)) and Path(module).is_file():
            name = Path(module).stem
            module = '{}'.format(Path(module))
        elif isinstance(module, str):
            name = module.split('.')[-1]
        else:
            name = module.__name__.split('.')[-1]
            module = module.__name__
        name = ''.join([m.title() for m in name.split('_')])

        return type(name, (cls,), {})(module)

    def _load_module(self):
        """Load simulation module (hidden)"""
        if Path(self._module).is_file():
            fname = Path(self._module)
            # https://stackoverflow.com/questions/19009932/import-arbitrary-python-source-file-python-3-3
            spec_file = importlib.util.spec_from_file_location(fname.stem, fname)
            spec_module = importlib.util.module_from_spec(spec_file)
            spec_file.loader.exec_module(spec_module)
            return spec_module

        return importlib.import_module(self._module)

    def restart(
            self,
            restart: Any,
            config: Optional[Dict[str, Any]]=None,
        ) -> bool:
        """Run the simulation module's ``restart`` method."""
        if self.has_restart:
            return self.run(config=config, restart=restart)

        raise NotImplementedError("Simulation module does not define 'restart' method")

    def run(
            self,
            config: Optional[Dict[str, Any]]=None,
            restart: Optional[Any]=None,
            **kwargs: str
        ) -> bool:
        """Run the simulation module's ``run`` method.

        This :meth:`run` method is used to call the simulation module's run method.
        If a simulation object ``sim`` was created with simulation module
        ``minimal``, then calls this :meth:`run` method calls ``run`` method in
        simulation module ``minimal``. A simple usage example is:

        .. code-block:: Python

            sim.run()

        Arguments:
            config: Configuration used for simulation
            restart: Data used for restart
            **kwargs: Optional parameters passed to the simulation
        """
        module = self._load_module()
        self.data = None

        if kwargs:
            warnings.warn("Keyword arguments are deprecated and ignored", DeprecationWarning)

        setup = module.defaults()
        if config:
            setup.update(config)
        config = Parser(setup)

        if restart is None:
            self.data = module.run(**config)
        else:
            self.data = module.restart(restart, **config)

    def defaults(self) -> Dict[str, Any]:
        """Pass-through returning simulation module defaults as a dictionary"""
        module = self._load_module()
        return module.defaults()

