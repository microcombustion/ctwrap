"""Parser module."""
import os
from typing import Optional, Dict, Any, Tuple, KeysView, Union
import json
from pint import UnitRegistry
from copy import deepcopy
from ruamel import yaml
import h5py


ureg = UnitRegistry()

__all__ = ['Parser', 'load_yaml', 'save_metadata']


class Parser(object):
    """
    A lightweight class that handles units.

    The handling mimics that of a python dictionary, while adding direct access to
    keyed values via attributes.
    """

    def __init__(self, dct: Dict[str, Any]) -> None:
        """
        Constructor

        Argument:
            dct (dict) : dictionary to be parsed
        """

        self.raw = dct

    def __getattr__(self, attr: str) -> str:
        """
        Get attribute

        Arguments:
             attr (str): attribute

        Returns:
            Atrribute
        """

        if attr not in self.raw:
            raise AttributeError("unknown attribute '{}'".format(attr))

        return self[attr]

    def __getitem__(self, key: str) -> Union[str, bool, float, Tuple]:
        """
        Get item

        Argument:
            key (str): key

        Returns:
            Corresponding values from the key

        """

        val = self.raw[key]

        if isinstance(val, (str, bool, int, float)):
            return val
        elif isinstance(val, list) and len(val) > 0:
            return ureg.Quantity(val[0], ureg[val[1]])

    def __repr__(self):
        return repr(self.raw)

    def keys(self) -> KeysView[str]:
        """
        Returns list of keys
        """
        return self.raw.keys()


def load_yaml(fname: str,
              path: Optional[str] = None,
              keys: Optional[str] = None) -> Tuple[Any, ...]:
    """
    Load yaml from file

    Arguments:
        fname (str) : file name
        path (str) : relative/absolute path. Empty ('') for
        keys (str) : key
    Returns:
        Dictionary containing the required keys
    """

    if path not in ['', None]:
        fname = (os.sep).join([path, fname])

    with open(fname) as yml:
        out = yaml.load(yml, Loader=yaml.SafeLoader)

    if keys is None:
        return out
    else:
        return tuple([deepcopy(out[k]) for k in keys])


def save_metadata(output: Dict[str, Any],
                  metadata: Dict[str, Any]) -> None:
    """
    Function save metadata as attributes to file

    Arguments:
        output (dict): file information
        metadata (dict): metadata
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
