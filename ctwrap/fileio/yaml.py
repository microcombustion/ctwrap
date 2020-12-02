"""Function handling file input/output."""

import os
from typing import Optional, Dict,Any
import json
from copy import deepcopy
from ruamel import yaml

import h5py



__all__ = ['load_yaml', 'save_metadata']


def load_yaml(fname: str,
              path: Optional[str] = None,
              keys: Optional[str] = None) -> Dict[str, Any]:
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

    with h5py.File(oname, 'r+') as f:
        for key, val in metadata.items():
            if isinstance(val, dict):
                f.attrs[key] = json.dumps(val)
            else:
                f.attrs[key] = val
