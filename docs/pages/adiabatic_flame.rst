Adiabatic Flame Batch
=====================

YAML Defaults
-------------

.. literalinclude:: ../../ctwrap/defaults/adiabatic_flame.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/adiabatic_flame.py
   :language: python

Running a Batch Simulation
--------------------------

An example for a batch simulation is given by the YAML configuration

.. literalinclude:: ../../yaml/adiabatic_flame.yaml
   :language: yaml

A parallel batch job for adiabatic flame calculations using this
configuration and the simulation module above can be run as:

.. code-block::

    $ ctwrap run adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.
