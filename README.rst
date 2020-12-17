|ci| |tag|

======
ctwrap
======

Light-weight Python wrapper for batch simulation jobs (e.g. Cantera).

-------------
Documentation
-------------

* `Sphinx documentation <https://microcombustion.github.io/ctwrap/>`_
* `jupyter notebooks <pages/jupyter.html>`_. An overview is given
  by a `minimal example <pages/minimal_example.html>`_.

----------
Philosophy
----------

The code was developed with the following objectives in mind. It should:

* create a flexible framework for generic simulations
* provide a command line interface
* be easily scriptable (using YAML configuration files via `ruamel.yaml`)
* enforce units (via `pint <https://pint.readthedocs.io/en/stable/>`_)
* avoid clutter (data are saved in HDF containers)
* enable parallel execution of (single-threaded) simulations (via `multiprocessing`)
* enable simple re-import of simulation results into native Cantera objects

-----
Usage
-----

A parallel batch job for adiabatic flame calculations with parameter variations
(for this example, a variation of equivalence ratio with 12 cases).
See `adiabatic_flame <pages/adiabatic_flame.html>`_
(modified from Cantera's
`adiabatic_flame example <https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/
examples/onedim/adiabatic_flame.py>`_). The configuration file consists three parts,
``strategy`` which contains parameter variation information, ``output`` which contains the
output file information and ``defaults`` which contains the default input parameters needed
to run the simulation module.
This can be run as:

.. code-block::

    $ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.

A batch job for a simulation module ``some_simulation.py`` with
configuration file ``batch_configuration.yaml`` can be run by:

.. code-block::

   $ ctwrap some_simulation.py batch_configuration.yaml --parallel

*Note:* the wrapper itself does not depend on a Cantera installation; only the
simulation modules do.

.. |ci| image:: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :target: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :alt: GitHub action

.. |tag| image:: https://img.shields.io/github/v/tag/microcombustion/ctwrap
   :target: https://github.com/microcombustion/ctwrap/tags
   :alt: GitHub tag (latest by date)
