Adiabatic Flame Batch
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

.. literalinclude:: ../../yaml/freeflame.yaml
   :language: yaml

A parallel batch job for adiabatic flame calculations using this
configuration and the simulation module above can be run as:

.. code-block::

    $ ctwrap run freeflame freeflame.yaml --parallel

Results are written to a single file ``freeflame.h5``.
