Ignition Batch Jobs
===================

YAML Defaults
-------------

.. literalinclude:: ../../ctwrap/defaults/ignition.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/ignition.py
   :language: python

Running a Batch Simulation
--------------------------

An example for a batch simulation is given by the YAML configuration

.. literalinclude:: ../../ctwrap/yaml/ignition.yaml
   :language: yaml

A parallel batch job for ignition calculations using the configuration and the simulation
module above can be run as:

.. code-block::

    $ ctwrap run ignition ignition.yaml --parallel

Results are written to a single file ``ignition.h5``.
