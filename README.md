# ctwrap

Light-weight Python wrapper for batch simulations (e.g. Cantera).

## Philosophy

The code was developed with the following objectives in mind. It should:

 * Create a flexible framework for generic simulations
 * Provide a command line interface
 * Be easily scriptable (using YAML configuration files via `ruamel.yaml`)
 * Enforce units (via `pint`)
 * Generate self-documenting results (data is saved in HDF containers via `pandas`)
 * Enable parallel execution of (single-threaded) simulations (via `multiprocessing`)

Caveat: the documentation of the initial release is limited to rudimentary docstrings, plus usage examples in the form of jupyter notebooks.

## Installation

### Clone/Install Repository

The following uses `pip` to install a (linked) version within a python environment (e.g. Anaconda).

```
$ git clone https://github.com/ischg/ctwrap.git
$ cd ctwrap
$ pip install .
```

### Update

Within the `ctwrap` source folder, run:

```
$ git pull
$ python setup.py develop
```

### Uninstall

```
$ pip uninstall ctwrap
```

