# ctwrap

Light-weight Python wrapper for batch simulations (e.g. Cantera).

## Philosophy

The code was developed with the following objectives in mind. It should:

 * create a flexible framework for generic simulations
 * provide a command line interface
 * be easily scriptable (using YAML configuration files via `ruamel.yaml`)
 * enforce units (via `pint`)
 * avoid clutter (data are saved in HDF containers)
 * results can be easily processed (via `pandas` HDF implementation)
 * generate self-documenting results (save configuration with results)
 * enable parallel execution of (single-threaded) simulations (via `multiprocessing`)

__Example:__ a parallel batch job for adiabatic flame calculations uses the simulation module `[adiabatic_flame](ctwrap/modules/adiabatic_flame.py)` (modified from Cantera's `[adiabatic_flame](https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/examples/onedim/adiabatic_flame.py)` example) with parameters defined in `[adiabatic_flame.yaml](ctwrap/examples/adiabatic_flame.yaml)`. This can be run as:
```
$ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel
```
Results (including configuration) are written to a single file `adiabatic_flame.h5`.

__Note__: the wrapper itself does not depend on a Cantera installation; only the simulation modules do.

__Caveat:__ the documentation of the initial code is limited to rudimentary docstrings, plus usage examples in the form of [jupyter notebooks](ctwrap/examples).

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

