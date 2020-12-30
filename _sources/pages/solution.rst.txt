Solution Batch Jobs
===================

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/solution.py
   :language: python

Running a Batch Simulation
--------------------------

An example for a batch simulation is given by the YAML configuration

.. literalinclude:: ../../yaml/solution.yaml
   :language: yaml

A parallel batch job for solution calculations using the configuration and the simulation
module above can be run as:

.. code-block::

    $ ctwrap run solution solution.yaml --parallel

Results are written to a single file ``solution.h5``.
