.. image:: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
       :target: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg

======
ctwrap
======

Light-weight Python wrapper for batch simulation jobs (e.g. Cantera). The source
code is available at the `ctwrap Github repositiory <https://github.com/microcombustion/ctwrap/>`_.

+++++++++++++
Documentation
+++++++++++++

* `Sphinx documentation <https://microcombustion.github.io/ctwrap/>`_
* `jupyter notebooks <pages/jupyter.html>`_. An overview is given
  by a `minimal example <pages/minimal_example.ipynb>`_.

++++++++++
Philosophy
++++++++++

The code was developed with the following objectives in mind. It should:

 * create a flexible framework for generic simulations
 * provide a command line interface
 * be easily scriptable (using YAML configuration files via `ruamel.yaml`)
 * enforce units (via `pint <https://pint.readthedocs.io/en/stable/>`_)
 * avoid clutter (data are saved in HDF containers)
 * enable parallel execution of (single-threaded) simulations (via `multiprocessing`)
 * enable simple re-import of simulation results into native Cantera objects

*Example:* a parallel batch job for adiabatic flame calculations uses the simulation module
`adiabatic_flame <pages/adiabatic_flame.py>`_
(modified from Cantera's
`adiabatic_flame example <https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/
examples/onedim/adiabatic_flame.py>`_) with parameters defined in `adiabatic_flame.yaml <pages/adiabatic_flame.yaml>`_
(for this example, a variation of equivalence ratio with 12 cases).
This can be run as::

    $ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.

Adapting custom simulation tasks to be used with ctwrap is straight-forward,
and mainly involves the creation of a Python module that largely reflects a
regular simulation script for a single set of parameter values.

*Alternatives*

Parameter variations can always be run in custom loops.

*Note:* the wrapper itself does not depend on a Cantera installation; only the
simulation modules do.
