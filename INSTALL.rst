+++++++++++++++++
Installing ctwrap
+++++++++++++++++

To install ctwrap, we strongly recommend using a ``conda`` (anaconda or miniconda) environment.
Dependencies for a fully functional environment are listed in the ``environment.yml`` file in
the root folder of the repository.

.. literalinclude:: ../environment.yml
   :language: yaml

+++++++++++++++++
Conda environment
+++++++++++++++++

To install, provide the ``environment.yml`` configuration to ``conda``, i.e.

.. code-block::

   $ conda env create -f environment.yml
   $ conda activate ctwrap

++++++++++++++++++++++++++++
Clone Repository and Install
++++++++++++++++++++++++++++

The following uses ``pip`` to install ``ctwrap`` within your
python environment (e.g. Anaconda).

.. code-block::

    $ git clone https://github.com/microcombustion/ctwrap.git
    $ cd ctwrap
    $ pip install .


For a linked installation, run ``pip install -e .`` instead.

++++++
Update
++++++

Within the ``ctwrap`` source folder, run

.. code-block::

    $ git pull
    $ python setup.py develop



+++++++++
Uninstall
+++++++++

.. code-block::

    $ pip uninstall ctwrap
