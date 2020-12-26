|ci| |tag|

======
ctwrap
======

Light-weight Python wrapper for batch simulation jobs (e.g. Cantera).

-------------
Documentation
-------------

`Sphinx documentation <https://microcombustion.github.io/ctwrap/>`_ includes:

* A brief summary (see `Overview <https://microcombustion.github.io/ctwrap/overview.html>`_),
* Typical batch simulation descriptions (see `Batch Jobs <https://microcombustion.github.io/ctwrap/pages/batch.html>`_), and
* `Jupyter Notebooks <https://microcombustion.github.io/ctwrap/examples/jupyter.html>`_ with illustrated examples.

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

-------
Example
-------

A parallel batch job for adiabatic flame calculations uses the
`adiabatic_flame <https://microcombustion.github.io/ctwrap/pages/adiabatic_flame.html>`_
module (modified from Cantera's |adiabatic flame|_ example). Based on the
YAML configuration given as a reference, a variation of 12 equivalence ratio values
is run as:

.. code-block::

    $ ctwrap run adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.

In general, a custom batch job requires a simulation module ``some_simulation.py`` and
a configuration file ``batch_configuration.yaml``. The corresponding batch job is run as:

.. code-block::

   $ ctwrap run some_simulation.py batch_configuration.yaml --parallel

Results are written to a single file ``some_simulation.h5``.

.. note:: the wrapper itself does not depend on a Cantera installation; only the
   simulation modules do.

.. |adiabatic flame| replace:: ``adiabatic_flame.py``
.. _adiabatic flame: https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/examples/onedim/adiabatic_flame.py

.. |ci| image:: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :target: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :alt: GitHub action

.. |tag| image:: https://img.shields.io/github/v/tag/microcombustion/ctwrap
   :target: https://github.com/microcombustion/ctwrap/tags
   :alt: GitHub tag (latest by date)
