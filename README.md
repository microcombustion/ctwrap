# cantera-wrapper

Wrapper functions for batch Cantera simulations.

## Installation

### Clone/Install Repository

The following uses `pip` to install a (linked) version within a python environment (e.g. Anaconda).

```

$ git clone https://github.com/ischg/cantera-wrapper.git
$ cd cantera-wrapper
$ pip install -e .
```

### Update

Within the `cantera-wrapper` source folder, run:

```
$ git pull
$ python setup.py develop
```

### Uninstall

```
$ pip uninstall ctwrap
```

## Dependencies

Requires cantera. Using the anaconda packager, it is installed via:

```
conda update --all
conda install -c cantera cantera
conda clean -t
```
