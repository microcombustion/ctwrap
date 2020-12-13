"""Parser module."""
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, KeysView, Generator, Union
import json
from pint import UnitRegistry
from copy import deepcopy
from ruamel import yaml
import h5py
import warnings
import re


__all__ = ['Parser', 'load_yaml', 'save_metadata']


ureg = UnitRegistry()


def _parse(val: str):
    """Parse string expression containg value and unit

    Arguments:
       val: String expression

    Returns:
       `Tuple` containing value and unit
    """

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


class Parser(object):
    """A lightweight class that handles units.

    The handling mimics that of a python dictionary, while adding direct access to
    keyed values via attributes.

    Arguments:
        raw: Dictionary to be parsed
    """

    def __init__(self, raw: Dict[str, Any]) -> None:
        """Constructor"""
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
        out = {key: Parser(val) for key, val in self.raw.items()}
        return out.values()

    def items(self):
        """Return parser items"""
        out = {key: Parser(val) for key, val in self.raw.items()}
        return out.items()

    @classmethod
    def from_yaml(
            cls,
            yml: str,
            path: Optional[str]=None,
            keys: Optional[str]=None) -> 'Parser':
        """Load parser from YAML

        Arguments:
            yml: File name or YAML string
            path: Relative/absolute path. Empty ('') for
            keys: List of keys
        """
        fname = Path(yml)
        if path is not None:
            fname = Path(path) / fname

        try:
            _ = fname.is_file() # will raise error
            with open(fname) as stream:
                out = yaml.load(stream, Loader=yaml.SafeLoader)
        except OSError:
            out = yaml.load(yml, Loader=yaml.SafeLoader)

        if keys is None:
            return cls(out)

        return cls({k: out[k] for k in keys})

    def to_yaml(self):
        """Convert Parser content to YAML string"""
        return yaml.dump(self.raw, Dumper=yaml.SafeDumper)

    def get(self, key, default=None):
        """Get key"""
        if key in self:
            return self[key]
        if default:
            return default
        return None


def save_metadata(output: Dict[str, Any],
                  metadata: Dict[str, Any]) -> None:
    """Function save metadata as attributes to file

    Arguments:
        output: file information
        metadata: metadata
    """

    oname = output['file_name']
    opath = output['path']
    formatt = output['format']
    force = output['force_overwrite']

    if oname is None:
        return
    if opath is not None:
        oname = os.path.join(opath, oname)

    with h5py.File(oname, 'r+') as hdf:
        for key, val in metadata.items():
            if isinstance(val, dict):
                hdf.attrs[key] = json.dumps(val)
            else:
                hdf.attrs[key] = val

    return
