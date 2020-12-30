Batch Jobs
==========

Beyond the `Minimal Example <../overview.rst>`__, ``ctwrap`` supports
the following pre-configured simulation modules:

.. toctree::
    :maxdepth: 2

    Equilibrium <equilibrium.rst>
    Free Flame <freeflame.rst>
    Ignition <ignition.rst>
    Solution <solution.rst>

Custom Simulations
++++++++++++++++++

In addition, ``ctwarp`` supports custom batch simulation. In general,
a custom batch job requires a simulation module ``some_simulation.py`` and
a configuration file ``batch_configuration.yaml``. The corresponding batch job is run as:

.. code-block::

   $ ctwrap run some_simulation.py batch_configuration.yaml --parallel

Depending on the configuration, results are written to a single file
``some_simulation.h5`` or ``some_simulation.csv``.