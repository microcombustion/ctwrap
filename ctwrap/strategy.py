""""Module defining batch simulation strategies"""

import warnings
from copy import deepcopy
from typing import Dict, Any, List, Optional

from .parser import _parse, _write, Parser


def _replace_entry(nested, key_list, value):
    """Locate and replace entry in nested dictionary (recursive)

    Arguments:
       nested: Multi-level (nested) dictionary
       key_list: Sequence of keys leading to entry of interest
       value: Entry to replace
    """
    if key_list[0] not in nested:
        return nested

    sub = nested[key_list[0]]
    if len(key_list) == 1:
        if isinstance(sub, list):
            sub[0] = value
        elif isinstance(sub, str):
            _, unit = _parse(sub)
            sub = _write(value, unit)
        else:
            sub = value
    else:
        sub = _replace_entry(sub, key_list[1:], value)
    nested[key_list[0]] = sub
    return nested


def _sweep_matrix(defaults, tasks):
    """Replace entries along multiple axes (recursive)

    Arguments:
       defaults: Default parameters
       tasks: Dictionary of variations
    """
    key = list(tasks.keys())[0]
    values = tasks.pop(key)
    entry = key.split('.')

    out = []
    for value in values:
        new = _replace_entry(deepcopy(defaults), entry, value)
        if tasks:
            out.extend(_sweep_matrix(new, tasks.copy()))
        else:
            out.append(new)

    return out


class Strategy:
    """Base class for batch simulation strategies"""

    def __init__(self, value={}):
        self._check_input(value, 0)
        warnings.warn("Base clase does not implement batch simulation strategy")

    @staticmethod
    def _check_input(value: Dict[str, Any], min_length: int, exact: Optional[bool]=True):
        """Check validity of input"""
        if not isinstance(value, dict):
            raise TypeError("Strategy needs to be defined by a dictionary")
        if exact and len(value) != min_length:
            raise ValueError("Invalid length: dictionary requires exactly "
                             "{} entry/entries.".format(min_length))
        elif len(value) < min_length:
            raise ValueError("Invalid length: dictionary requires at least "
                             "{} entry/entries.".format(min_length))
        return True

    @classmethod
    def load(cls, **strategy):
        """Factory loader for strategy objects

        **Example:** The following code creates a `Sequence` object *strategy* that varies
        the variable *foobar*. The dictionary key at the top level specifies what strategy
        object is being loaded:

        .. code-block:: Python

           strategy = ctwrap.Strategy.load(sequence={'foobar': [0, 1, 2, 3]})

        Arguments:
           **strategy: Keywords with single key/value pair, where the lower-case key
              specifies the batch simulation strategy and the value holds parameters.
              Except for the case, the key needs to match the name of a `Strategy` object.

        Returns:
           Instantiated `Strategy` object
        """
        key, value = list(strategy.items())[0]

        hooks = {'strategy': cls}
        for sub in cls.__subclasses__():
            hooks[sub.__name__.lower()] = sub

        if key not in hooks:
            raise NotImplementedError("Unknown strategy '{}'".format(key))

        cls_hook = hooks[key]
        return type(cls_hook.__name__, (cls_hook, ), {})(value)

    def create_tasks(self, defaults: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create list of parameter sets for a parameter variation

        **Example:** The following code applies a parameter variation to the
        `Sequence` object *strategy* based on a parameter set *defaults*:

        .. code-block:: Python

           # define parameter variation
           foo = {'foobar': [0, 1, 2, 3]}
           strategy = ctwrap.Sequence(foo)

           # generate list of tasks based on default parameters
           defaults = {'foobar': 1, 'spam': 2.0, 'eggs': 3.14}
           tasks = strategy.create_tasks(defaults)

        Arguments:
           defaults: Dictionary containing default parameters

        Returns:
           List of dictionaries with parameter variation
        """
        raise NotImplementedError("Needs to be implemented by derived classes")


class Sequence(Strategy):
    """Variation of a single parameter

    Arguments:
       sweep: Dictionary specifying single parameter sequence
    """

    def __init__(self, sweep: Dict[str, Any]):
        self._check_input(sweep, 1)
        self.sweep = sweep

    @classmethod
    def from_legacy(cls, items):
        """Create Sequence from ctwrap 0.1.0 sytax"""
        return cls({items['entry']: items['values']})

    def create_tasks(self, defaults):
        ""
        return _sweep_matrix(defaults, self.sweep)


class Matrix(Strategy):
    """Variation of multiple parameters

    Arguments:
       matrix: Dictionary specifying multiple parameter sequences
    """

    def __init__(self, matrix):
        self._check_input(matrix, 2, False)
        self.matrix = matrix

    def create_tasks(self, defaults):
        ""
        return _sweep_matrix(defaults, self.matrix)


class Sobol(Strategy):
    """Pseudo-randomly sampled parameter space via Sobol sequence

    Not implemented; there is prior work in Ayoobi and Schoegl, PROCI 2015
    """
    # Note: old work is Python 2 / Cantera 2.1

    def __init__(self, ranges):
        self._check_input(ranges, 1, False)
        self.ranges = ranges

    # def create_tasks(self):
    #     raise NotImplementedError("tbd")
