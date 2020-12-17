========
Overview
========

Ctwrap is a light-weight batch simulation wrapper written in Python. The wrapper consists of three classes:
the :any:`parser` class is used to parsed the input file and also
handles units using `pint <https://pint.readthedocs.io/en/stable/>`_,
the :any:`Simulation` that wraps a simulation module to be run.
More details about the module is discussed below and the
:any:`SimulationHandler` that handles parameter variations and switches between
multiple configurations.

Simulation Module
-----------------

The wrapper requires a simulation module, a single run python module, that should consists of three
methods: ``defaults``, ``run`` and ``save``. This isn't much different from a convention script, all that is
done is that  the code is `organized`.
The ``defaults`` method should return the default input parameters.
The ``run`` method runs a single simulation and returns a dictionary containing the output object.
The save method saves the output object based on the specified
format in the YAML input file. See the ``minimal`` module below.

.. literalinclude:: ../ctwrap/modules/minimal.py
   :language: python

YAML Configuration
------------------

The inputs are passed through a YAML file. The yaml is structured into three parts: ``strategy``,
``output``, and ``defaults``.  The ``strategy`` contains information about the variation. At the moment
``ctwrap`` only supports sequence and matrix specification. The values
can be specified as a list or alternatively using modes such as numpy
`arange <https://numpy.org/doc/stable/reference/generated/numpy.arange.html>`_ or
`linspace <https://numpy.org/doc/stable/reference/generated/numpy.linspace.html#numpy.linspace>`_
The ``output`` contains information about the resulting file to be
saved  such as the ``file_name``, ``path`` etc. The ``output`` is optional, and in that case,
the file is saved with the name of the module to be run. The ``defaults`` contains the defaults
input required to run the simulation module. See the ``minimal`` yaml below.

.. literalinclude:: ../yaml/minimal.yaml
   :language: yaml

Run Batch Job
-------------

A parallel batch job for adiabatic flame calculations with parameter variations
(for this example, a variation of equivalence ratio with 12 cases).
See `adiabatic_flame <pages/adiabatic_flame.html>`_
(modified from Cantera's
`adiabatic_flame example <https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/
examples/onedim/adiabatic_flame.py>`_) ).
This can be run as:

.. code-block::

    $ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.


*Note*: ``ctwrap`` only saves in `h5` format.
