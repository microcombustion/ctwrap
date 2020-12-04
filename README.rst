

.. image:: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
       :target: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg

======
ctwrap
======

Light-weight Python wrapper for batch simulation jobs (e.g. Cantera). The source
code is available at the `ctwrap Github repositiory <https://github.com/microcombustion/ctwrap/>`_.

++++++++
Overview
++++++++
Ctwrap is a light-weight batch simulation wrapper written in Python. The wrapper consists of two modules:
the ``parser`` and the ``simulation`` modules. The ``parser`` module is used to parsed the input file and also
handles units using `pint <https://pint.readthedocs.io/en/0.10.1/_modules/pint/registry.html/>`_,  while
the ``simulation`` modules handles running batch operation. The ``simulation`` module consists of two classes:
the :py:class:`~ctwrap.simulation.Simulation` that wraps a simulation module to be run.
More details about the module is discussed below and the
:py:class:`~ctwrap.simulation.SimulationHandler` that handles parameter variations and switches between
multiple configurations.

The wrapper requires a simulation module, a single run python module, that should consists of three
methods: ``defaults``, ``run`` and ``save``. See `minimal module <./ctwrap/modules/minimal.py>`_.
The ``defaults`` method should return the default input parameters.
The ``run`` method runs a single simulation and returns a dictionary containing the output object.
The save method saves the output object based on the specified
format in the yaml input file.

The inputs are passed through a yaml file. The yaml is structured into three parts: ``output``,
``variation`` and ``defaults``. The ``output`` contains information about the resulting file to be
saved  such as the ``file_name``, ``format`` etc. The ``file_name`` is optional, and in that case,
the file is saved with the name of the module to be run. The ``variation`` contains ``entry``
and ``values`` to be varied, while the ``defaults`` contains the defaults input required to run
the module see `minimal yaml <./examples/minimal.yaml>`_.

+++++++++++++
Documentation
+++++++++++++

* `Sphinx documentation <https://microcombustion.github.io/ctwrap/>`_
* `jupyter notebooks <./examples/>`_. An overview is given
  by a `minimal example <./examples/minimal_example.ipynb>`_.

++++++++++
Philosophy
++++++++++

The code was developed with the following objectives in mind. It should:

 * create a flexible framework for generic simulations
 * provide a command line interface
 * be easily scriptable (using YAML configuration files via `ruamel.yaml`)
 * enforce units (via `pint`)
 * avoid clutter (data are saved in HDF containers)
 * results can be easily processed (via `pandas` HDF implementation)
 * generate self-documenting results (save configuration with results)
 * enable parallel execution of (single-threaded) simulations (via `multiprocessing`)

*Example:* a parallel batch job for adiabatic flame calculations uses the simulation module
`adiabatic_flame <./ctwrap/modules/adiabatic_flame.py/>`_
(modified from Cantera's
`adiabatic_flame example <https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/
examples/onedim/adiabatic_flame.py>`_) with parameters defined in `adiabatic_flame.yaml <./ctwrap/examples/adiabatic_flame.yaml>`_
(for this example, a variation of equivalence ratio with 12 cases).
This can be run as::

    $ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel

Results (including configuration) are written to a single file `adiabatic_flame.h5`.

*Note:* the wrapper itself does not depend on a Cantera installation; only the
simulation modules do.
