========
Overview
========

Ctwrap is a light-weight batch simulation wrapper written in Python. The wrapper consists of
two main classes:

* the :any:`Simulation` class that wraps a simulation module to be run, and
* the :any:`SimulationHandler` class that handles parameter variations and switches between
  multiple configurations.

Parameter variations are based on a YAML configuration file, where the auxiliary
:any:`Parser` class is used to parsed the input file and also
handles units using `pint <https://pint.readthedocs.io/en/stable/>`_. In addition, the
:any:`Strategy` class specifies how the parameter variation is run.

Simulation Module
-----------------

The wrapper requires a simulation module, - written as a single run python module, - that defines two
methods: ``defaults`` and ``run``. The layout similar to a conventional script, the main difference
is that the code is `organized`. Specifically:

* The ``defaults()`` method returns default input parameters.
* The ``run()`` method runs a single simulation and returns a dictionary containing the output object.

The structure of a simulation module is illustrated by the following *minimal example*:

.. literalinclude:: ../ctwrap/modules/minimal.py
   :language: python

YAML Configuration
------------------

The inputs are passed through a YAML configuration file. The YAML input has three main fields: ``strategy``,
``output``, and ``defaults``.

* The ``strategy`` entry contains information about the variation. At the moment
  ``ctwrap`` supports :any:`Sequence` and :any:`Matrix` specifications. The values
  can be specified as a list or alternatively using modes such as numpy
  `arange <https://numpy.org/doc/stable/reference/generated/numpy.arange.html>`_ or
  `linspace <https://numpy.org/doc/stable/reference/generated/numpy.linspace.html#numpy.linspace>`_.
* The ``output`` entry contains information about the resulting file to be
  saved  such as the ``file_name``, ``path`` etc. The ``output`` is optional, and in that case,
  the file is saved with the name of the module to be run.
* The ``defaults`` entry contains default inputs required to run the simulation module.
* The ``ctwrap`` entry indicates the minimum ``ctwrap`` revision that supports the YAML format

The structure of a YAML configuration file is illustrated by the following *minimal example*:

.. literalinclude:: ../yaml/minimal.yaml
   :language: yaml

Running a Batch Job
-------------------

A parallel batch job for the minimal example using the configuration and the simulation
module above can be run from the command line as:

.. code-block::

    $ ctwrap run minimal minimal.yaml --parallel
