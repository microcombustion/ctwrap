Equilibrium Batch Simulation
============================

YAML Defaults
-------------

.. literalinclude:: ../../ctwrap/defaults/equilibrium.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/equilibrium.py
   :language: python

Running the Batch Simulation
----------------------------

An example for a batch simulation is given by the YAML configuration

.. literalinclude:: ../../yaml/equilibrium.yaml
   :language: yaml

A parallel batch job for equilibrium calculations using the configuration and the simulation
module above can be run as:

.. code-block::

    $ ctwrap equilibrium equilibrium.yaml --parallel

Results are written to a single file ``equilibrium.csv``.
