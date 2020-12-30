+++++++++++++++++
Base Installation
+++++++++++++++++

The simplest approach is to install ``ctwrap`` from the Python Package
Index (PyPI), i.e.

.. code-block::

   $ pip install ctwrap

.. note::

   ``ctwrap`` itself does not depend on a Cantera installation (only simulation
   modules do). It is recommended to install Cantera before ``ctwrap`` in a
   separate step.

+++++++++++++++++
Full Installation
+++++++++++++++++

As an alternative to ``pip``, the full package (i.e. including test suite and
documentation) can be installed by cloning the GitHub repository. For this
approach, a ``conda`` (anaconda or miniconda) environment is strongly
recommended.

**Clone repository:** Use ``git`` to clone the repository, i.e.

.. code-block::

   $ git clone https://github.com/microcombustion/ctwrap.git
   $ cd ctwrap

Dependencies for a fully functional environment are listed in the ``environment.yml`` file in
the root folder of the repository.

.. literalinclude:: ../environment.yml
   :language: yaml

**Create Environment:** To create the enviroment, provide the
``environment.yml`` configuration to ``conda``, i.e.

.. code-block::

   $ conda env create -f environment.yml
   $ conda activate ctwrap

**Installation:** Use ``pip`` to install ``ctwrap`` within your python environment.

.. code-block::

    $ pip install .

For a linked installation, run ``pip install -e .`` instead.

**Update:** Within the ``ctwrap`` source folder, run

.. code-block::

    $ git pull
    $ python setup.py develop



**Uninstall:** To uninstall, simply remove the ``conda`` environment, i.e.

.. code-block::

    $ pip uninstall ctwrap
