Ignition Batch Simulation
=========================

YAML Configuration
******************

.. literalinclude:: ../../yaml/ignition.yaml
   :language: yaml

Simulation Module
******************

.. literalinclude:: ../../ctwrap/modules/ignition.py
   :language: python

*Example:* a parallel batch job for ignition calculations using the configuration and the simulation
module above can be run as:

.. code-block::

    $ ctwrap ignition ignition.yaml --parallel

Results are written to a single file ``ignition.h5``.
