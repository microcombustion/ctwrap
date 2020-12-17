Adiabatic Flame Batch
=====================

YAML Configuration
------------------

.. literalinclude:: ../../yaml/adiabatic_flame.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/adiabatic_flame.py
   :language: python

Run Batch Job
-------------

A parallel batch job for adiabatic flame calculations using the
configuration and the simulation module above can be run as:

.. code-block::

    $ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel

Results are written to a single file ``adiabatic_flame.h5``.
