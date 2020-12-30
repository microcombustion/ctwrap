.. ctwrap documentation master file, created by
   sphinx-quickstart on Sat Nov 28 09:13:11 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ctwrap - Wrapper for Batch Simulations
======================================

Python wrapper for batch simulations (e.g. Cantera).
The source code is available at the
`ctwrap Github repository <https://github.com/microcombustion/ctwrap/>`_.

|ci| |tag|

++++++++++++++++++
Table of Contents
++++++++++++++++++

.. toctree::
   :maxdepth: 1

      Installation <installation.rst>
      Overview <overview.rst>
      Batch Jobs <pages/batch.rst>
      Jupyter Notebooks <examples/jupyter.rst>
      API Reference <pages/api.rst>

Philosophy
----------

The software was developed with the following objectives in mind. It should:

* provide a low-level interface to essential |cantera|_ capabilities
* create a flexible framework for generic simulations
* provide a command line interface
* be easily scriptable (using YAML configuration files)
* enforce units (via |pint|_)
* enable parallel execution of (single-threaded) simulations (via |multiprocessing|_)
* enable simple re-import of simulation results into native Cantera objects

.. note:: Although core functions of this software are continuously tested, there
   may be remaining bugs, non-working features, or other issues that could prevent
   a user from using this software to their specification. If you find problems,
   please report them in the issue tracker.

Example
-------

A parallel batch job for adiabatic flame calculations uses the
`freeflame <https://microcombustion.github.io/ctwrap/pages/freeflame.html>`_
module (modified from Cantera's |adiabatic flame|_ example). Based on the
YAML configuration given as a reference, a variation of 12 equivalence ratio values
is run as::

    $ ctwrap run freeflame freeflame.yaml --parallel

Results are written to a single file ``freeflame.h5``.

.. |pint| replace:: ``pint``
.. _pint: https://pint.readthedocs.io/en/stable/

.. |multiprocessing| replace:: ``multiprocessing``
.. _multiprocessing: https://docs.python.org/3/library/multiprocessing.html

.. |cantera| replace:: ``cantera``
.. _cantera: https://cantera.org/

.. |adiabatic flame| replace:: ``adiabatic_flame.py``
.. _adiabatic flame: https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/examples/onedim/adiabatic_flame.py

.. |ci| image:: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :target: https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg
   :alt: GitHub action

.. |tag| image:: https://img.shields.io/github/v/tag/microcombustion/ctwrap
   :target: https://github.com/microcombustion/ctwrap/tags
   :alt: GitHub tag (latest by date)
