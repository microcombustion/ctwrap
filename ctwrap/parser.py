"""The :py:mod:`parser` module defines a convenience object :class:`Parser`, which
supports dimensions via ``pint`` for easy access to data defined in YAML
configuration files within ``ctwrap`` simulation modules.

Usage
+++++

The following illustration assumes configuration data stored using YAML syntax
in a file ``config.yaml`` with content:

.. code-block:: YAML

   defaults:
     upstream:
       T: 300. kelvin # temperature
       P: 1. atmosphere # pressure
       phi: .55 # equivalence ratio
       fuel: H2
       oxidizer: O2:1,AR:5
     chemistry:
       mechanism: h2o2.yaml
     domain:
       width: 30 millimeter # domain width

A :class:`Parser` object can be created via the class-method :meth:`from.yaml`,
which acts much like a dictionary that also includes access via attributes:

.. code-block:: Python

   defaults = Parser.from_yaml('config.yaml')
   keys = default.keys() # returns 'upstream', 'chemistry', 'domain'
   upstream = defaults.upstream # Parser containing 'upstream'

If dimensions are defined, entries are accessible as ``pint.quantity`` objects:

.. code-block:: Python

   defaults.upstream.P # returns "1.0 standard_atmosphere" (pint)
   upstream.P # equivalent
   upstream['P'] # equivalent
   upstream.P.to('pascal') # returns "101325.0 pascal" (pint)
   upstream.P.m_as('pascal') # returns 101325.0 (float)

If no dimensions are defined, entries are accessed as conventional dictionaries entries:

.. code-block:: Python

   upstream.phi # returns 0.55 (float)
   upstream.oxidizer # returns 'O2:1,AR:5' (str)

Underlying dictionaries and/or data are accessed via the ``raw`` attribute, i.e.

.. code-block:: Python

   defaults.raw # returns dictionary corresponding to original YAML
   defaults.raw['upstream']['P'] # returns '1. atmosphere' (str)
   defaults.upstream.raw['P'] # equivalent
   upstream.raw['P'] # equivalent
   upstream.raw['oxidizer'] # returns 'O2:1,AR:5' (str)

Class Definition
++++++++++++++++
"""
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, KeysView, Generator, Union
from copy import deepcopy
from pint import UnitRegistry
from ruamel.yaml import YAML
import warnings
import re


__all__ = ['Parser']


ureg = UnitRegistry()


def _parse(val: str):
    """Parse string expression containg value and unit

    Arguments:
       val: String expression

    Returns:
       `Tuple` containing value and unit
    """
    # TODO :seems parser does not handle "e" scientific notation e.g; "1e-6 m**3" is not parsed as dimensioned unit. 

    if not isinstance(val, str):
        raise TypeError("Method requires string input")

    value = re.findall(r'^([-+]?\d*\.\d*(?=\s)|\d+(?=\s))', val)
    if not (value and val[:len(value[0])] == value[0]):
        return val, None

    # string starts with value
    value = value[0]
    val = val[len(value):]

    val = val.strip()
    if val:
        unit = val
    else:
        unit = 'dimensionless'

    return value, unit


def _write(value: Union[int, float, str], unit: Optional[str]=None):
    """Format value / unit combination into parseable string

    Arguments:
       value: Value
       unit: String describing unit

    Returns:
       Formatted string
    """
    out = '{}'.format(value)

    if unit is not None and unit != 'dimensionless':
        out += ' {}'.format(unit)

    return out


def _update(value: Dict[str, Any], update: Dict[str, Any]):
    """Update entries in nested dictionaries (recursive)

    Arguments:
       value: Multi-level (nested) dictionary
       update: Dictionary containing updates
    """
    for key, val in update.items():

        if key not in value:
            value[key] = val
        elif isinstance(val, dict):
            value[key] = _update(value[key], val)
        else:
            value[key] = val
    return value


class Parser(object):
    """A lightweight class that handles units.

    The handling mimics that of a python dictionary, while adding direct access to
    keyed values via attributes.

    Arguments:
        raw: Dictionary to be parsed
    """

    def __init__(self, raw: Dict[str, Any]) -> None:
        """Constructor"""
        if isinstance(raw, Parser):
            raw = deepcopy(raw.raw)
        if not isinstance(raw, dict):
            raise TypeError("Cannot construct 'Parser' object from {} "
                            "with type '{}'".format(raw, type(raw)))
        self.raw = raw

    def __repr__(self):
        return repr(self.raw)

    def __getattr__(self, attr: str) -> str:
        """Make dictionary entries accessible as attributes"""

        if attr not in self.raw:
            raise AttributeError("unknown attribute '{}'".format(attr))

        return self[attr]

    def __getitem__(self, key: str) -> Union[str, bool, int, float, ureg.Quantity]:
        """Make class subscriptable"""
        val = self.raw[key]

        if isinstance(val, str):
            value, unit = _parse(val)
            if value and unit:
                return ureg.Quantity(val)
            return val

        if isinstance(val, dict):
            return Parser(val)

        if isinstance(val, (list, tuple)) and len(val) == 3:
            warnings.warn("Definition of values by lists/tuples is superseded by value/unit strings",
                          PendingDeprecationWarning)
            return ureg.Quantity(val[0], val[1])

        return val

    def __len__(self):
        """Length corresponds to number of keys"""
        return len(self.raw)

    def __eq__(self, other: 'Parser'):
        """Check equality"""
        if isinstance(other, Parser):
            return self.raw == other.raw
        return False

    def __iter__(self) -> Generator:
        """Returns itself as an iterator."""
        for k in self.raw.keys():
            yield k

    def __contains__(self, key: str) -> bool:
        """Check whether object contains channel."""
        return key in self.raw

    def keys(self) -> KeysView[str]:
        """Returns list of keys"""
        return self.raw.keys()

    def values(self):
        """Return parser values"""
        return dict(self.items()).values()

    def items(self):
        """Return parser items"""
        out = {
            key: Parser(val) if isinstance(val, dict) else self[key]
            for key, val in self.raw.items()
            }
        return out.items()

    @classmethod
    def from_yaml(
            cls,
            yml: str,
            defaults: Optional[bool]=False,
            path: Optional[str]=None,
            keys: Optional[str]=None) -> 'Parser':
        """Load parser from YAML

        Arguments:
           yml: File name or YAML string
           defaults: If `True`, load from ``ctwrap.defaults`` database
           path: Relative/absolute path
           keys: List of keys
        """
        fname = Path(yml)
        if defaults:
            # load from 'ctwrap/defaults' database
            fname = Path(__file__).parents[0] / 'defaults' / fname
        elif path is not None:
            fname = Path(path) / fname

        yaml = YAML(typ="safe")
        try:
            _ = fname.is_file()  # will raise error
            with open(fname) as stream:
                out = yaml.load(stream)
        except FileNotFoundError:
            raise FileNotFoundError("File '{}' not found".format(fname))
        except OSError:
            out = yaml.load(yml)

        if keys is None:
            return cls(out)

        return cls({k: out[k] for k in keys})

    def to_yaml(self):
        """Convert Parser content to YAML string"""
        yaml = YAML(typ="safe")
        return yaml.dump(self.raw, Dumper=yaml.SafeDumper)

    def get(self, key, default=None):
        """Get key"""
        if key in self:
            return self[key]
        if default:
            return default
        return None

    def update(self, new: Union[Dict, 'Parser']):
        """Update Parser object (recursive)

        Arguments:
           new: Object containing replacement values
        """
        if isinstance(new, Parser):
            new = new.raw
        elif not isinstance(new, dict):
            raise TypeError("Replacement value needs to be 'Parser' or 'dict', "
                            "not '{}".format(type(new)))

        self.raw = _update(self.raw, new)
