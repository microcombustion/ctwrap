![ci](https://github.com/microcombustion/ctwrap/workflows/CI/badge.svg)
![tag](https://img.shields.io/github/v/tag/microcombustion/ctwrap)
![PyPI](https://img.shields.io/pypi/v/ctwrap?color=lightblue)

# ctwrap

Python wrapper for batch simulations (e.g. Cantera).

## Documentation

[Sphinx documentation](https://microcombustion.github.io/ctwrap/>) includes:

* A brief summary (see [Overview](https://microcombustion.github.io/ctwrap/overview.html)),
* Typical batch simulation descriptions (see [Batch Jobs](https://microcombustion.github.io/ctwrap/pages/batch.html)), and
* [Jupyter Notebooks](https://microcombustion.github.io/ctwrap/examples/jupyter.html) with illustrated examples.

## Philosophy

The software was developed with the following objectives in mind. It should:

* provide a low-level interface to essential [`cantera`](https://cantera.org/)
  capabilities
* create a flexible framework for generic simulations
* provide a command line interface
* be easily scriptable (using YAML configuration files)
* enforce units (via [`pint`](https://pint.readthedocs.io/en/stable/))
* enable parallel execution of (single-threaded) simulations (via
  [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html))
* enable simple re-import of simulation results into native Cantera objects

> Although core functions of this software are continuously tested, there
  may be remaining bugs, non-working features, or other issues that could prevent a user from using this software to their specification. If you find problems, please report them in the issue tracker.

## Example

A parallel batch job for adiabatic flame calculations uses the
`freeflame` module (modified from Cantera's `adiabatic_flame.py` example). Based on the YAML configuration given as a reference, a variation of 12 equivalence ratio values is run as:

```
$ ctwrap run freeflame freeflame.yaml --parallel
```

Results are written to a single file `adiabatic_flame.h5`.
