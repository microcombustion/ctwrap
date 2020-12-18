========
Overview
========

Ctwrap is a light-weight batch simulation wrapper written in Python. The wrapper consists of three classes:
the :any:`Parser` class is used to parsed the input file and also
handles units using `pint <https://pint.readthedocs.io/en/stable/>`_,
the :any:`Simulation` that wraps a simulation module to be run.
More details about the module is discussed below and the
:any:`SimulationHandler` that handles parameter variations and switches between
multiple configurations.

Simulation Module
-----------------

The wrapper requires a simulation module, - written as a single run python module, - that defines three
methods: ``defaults``, ``run`` and ``save``. This isn't much different from a convention script, all that is
done is that  the code is `organized`. Specifically:

* The ``defaults()`` method should return the default input parameters.
* The ``run()`` method runs a single simulation and returns a dictionary containing the output object.
* The optional ``save()`` method saves the output object based on format specified
  by a YAML configuration file.

The structure of a simulation module is illustrated by the following *minimal example*:

.. literalinclude:: ../ctwrap/modules/minimal.py
   :language: python

YAML Configuration
------------------

The inputs are passed through a YAML configuration file. The YAML input has three main fields: ``strategy``,
``output``, and ``defaults``.

* The ``strategy`` contains information about the variation. At the moment
  ``ctwrap`` supports :any:`Sequence` and :any:`Matrix` specifications. The values
  can be specified as a list or alternatively using modes such as numpy
  `arange <https://numpy.org/doc/stable/reference/generated/numpy.arange.html>`_ or
  `linspace <https://numpy.org/doc/stable/reference/generated/numpy.linspace.html#numpy.linspace>`_.
* The ``output`` contains information about the resulting file to be
  saved  such as the ``file_name``, ``path`` etc. The ``output`` is optional, and in that case,
  the file is saved with the name of the module to be run.
* The ``defaults`` contains the defaults input required to run the simulation module.
* The ``ctwrap`` field indicates the minimum ``ctwrap`` revision that supports the YAML format

The structure of a YAML configuration file is illustrated by the following *minimal example*:

.. literalinclude:: ../yaml/minimal.yaml
   :language: yaml

Running a Batch Job
-------------------

A parallel batch job for the minimal example using the configuration and the simulation
module above can be run from the command line as:

.. code-block::

    $ ctwrap minimal minimal.yaml --parallel
