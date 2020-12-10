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

The wrapper requires a simulation module, a single run python module, that should consists of three
methods: ``defaults``, ``run`` and ``save``. This isn't much different from a convention script, all that is
done is that  the code is `organized`.
The ``defaults`` method should return the default input parameters.
The ``run`` method runs a single simulation and returns a dictionary containing the output object.
The save method saves the output object based on the specified
format in the YAML input file. See the ``minimal`` module below.

Simulation Module
******************

.. literalinclude:: ../ctwrap/modules/minimal.py
   :language: python

The inputs are passed through a YAML file. The yaml is structured into three parts: ``output``,
``variation`` and ``defaults``. The ``output`` contains information about the resulting file to be
saved  such as the ``file_name``, ``path`` etc. The ``file_name`` is optional, and in that case,
the file is saved with the name of the module to be run. The ``variation`` contains ``entry``
and ``values`` to be varied, while the ``defaults`` contains the defaults input required to run
the module. See the ``minimal`` yaml below.

YAML Configuration
******************

.. literalinclude:: ../yaml/minimal.yaml
   :language: yaml


*Note*: ``ctwrap`` only saves in `h5` format.
