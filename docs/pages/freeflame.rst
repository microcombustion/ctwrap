FreeFlame Batch Jobs
=====================

YAML Defaults
-------------

.. literalinclude:: ../../ctwrap/defaults/freeflame.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/freeflame.py
   :language: python

Running a Batch Simulation
--------------------------

An example for a batch simulation is given by the YAML configuration

.. literalinclude:: ../../ctwrap/yaml/freeflame.yaml
   :language: yaml

A parallel batch job for adiabatic flame calculations using this
configuration and the simulation module above can be run as:

.. code-block::

    $ ctwrap run freeflame freeflame.yaml --parallel --strategy sequence

or

.. code-block::

    $ ctwrap run freeflame freeflame.yaml --parallel --strategy matrix

where the *strategy* keyword corresponds to entries in the YAML file. In either case,
results are written to a single file ``freeflame.h5``.
