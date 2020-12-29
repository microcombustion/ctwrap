Equilibrium Batch Jobs
======================

YAML Defaults
-------------

.. literalinclude:: ../../ctwrap/defaults/equilibrium.yaml
   :language: yaml

Simulation Module
-----------------

.. literalinclude:: ../../ctwrap/modules/equilibrium.py
   :language: python

Running a Batch Simulation
--------------------------

The ``equilibrium`` simulation module allows for equilibrium calculations
of both single and multiple phases.

Single Phase
++++++++++++

An example for a batch simulation for a single thermodynamic phase is
given by the YAML configuration

.. literalinclude:: ../../yaml/equilibrium.yaml
   :language: yaml

A parallel batch job for equilibrium calculations using the configuration
and the simulation module above can be run as:

.. code-block::

    $ ctwrap run equilibrium equilibrium.yaml --parallel

Results are written to a single file ``equilibrium.csv``.

Multiple Phases
+++++++++++++++

An example for a batch simulation with multiple thermodynamic phases is
given by the YAML configuration

.. literalinclude:: ../../yaml/equilibrium_multi.yaml
   :language: yaml

A parallel batch job for equilibrium calculations using the configuration
and the simulation module above can be run as:

.. code-block::

    $ ctwrap run equilibrium equilibrium_multi.yaml --parallel

Results are written to a single file ``equilibrium_multi.csv``.
