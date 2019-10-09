# ctwrap

Light-weight Python wrapper for batch simulation jobs (e.g. Cantera).

> At the moment, the wrapper works on Linux, but not on Windows. Some features that are currently implemented in Cantera 2.5 (e.g. improved `SolutionArray` support with HDF export) will be incorporated in a future update. 

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

__Example:__ a parallel batch job for adiabatic flame calculations uses the simulation module [`adiabatic_flame`](ctwrap/modules/adiabatic_flame.py) (modified from Cantera's [`adiabatic_flame`](https://github.com/Cantera/cantera/blob/master/interfaces/cython/cantera/examples/onedim/adiabatic_flame.py) example) with parameters defined in [`adiabatic_flame.yaml`](ctwrap/examples/adiabatic_flame.yaml) (for this example, a variation of equivalence ratio with 12 cases). This can be run as:
```
$ ctwrap adiabatic_flame adiabatic_flame.yaml --parallel
```
Results (including configuration) are written to a single file `adiabatic_flame.h5`.

__Note__: the wrapper itself does not depend on a Cantera installation; only the simulation modules do.

__Caveat:__ the documentation of the initial code is limited to rudimentary docstrings, plus examples in the form of [jupyter notebooks](ctwrap/examples). An overview is given by a [minimal example](ctwrap/examples/minimal_example.ipynb). 

## Installation

### Clone/Install Repository

The following uses `pip` to install `ctwrap` within your python environment (e.g. Anaconda).

```
$ git clone https://github.com/ischoegl/ctwrap.git
$ cd ctwrap
$ pip install .
```
For a linked installation, run `pip install -e .` instead.

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

