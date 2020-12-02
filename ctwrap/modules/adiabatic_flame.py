""" Module to run adiabatic flame simulation"""

import os
import warnings
from typing import Dict, Any, Optional
from ruamel import yaml
import h5py

from ctwrap import Parser


try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)

__DEFAULTS = """\
# default parameters for the `freeflame` module
upstream:
  T: [300., kelvin, 'temperature']
  P: [1., atmosphere, 'pressure']
  phi: [.55, dimensionless, 'equivalence ratio']
  fuel: 'H2'
  oxidizer: 'O2:1.,AR:5'
chemistry:
  mechanism: h2o2.xml
domain:
  width: [30, millimeter, 'domain width']
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name: str,
        chemistry: Optional[Dict[str, Any]] = None,
        upstream: Optional[Dict[str, Any]] = None,
        domain: Optional[Dict[str, Any]] = None,
        loglevel: Optional[int] = 0) -> Dict[str, Any]:
    """
    Function handling adiabatic flame simulation.
    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        name (str): name of the task
        chemistry (dict): reflects yaml 'configuration:chemistry'
        upstream  (dict): reflects yaml 'configuration:upstream'
        domain    (dict): reflects yaml 'configuration:simulation'
        loglevel   (int): amount of diagnostic output (0 to 8)

    Returns:
        Dictionary containing Cantera `Flamebase` object
    """

    # initialize

    # IdealGasMix object used to compute mixture properties, set to the state of the
    # upstream fuel-air mixture
    mech = Parser(chemistry).mechanism
    gas = ct.Solution(mech)

    # temperature, pressure, and composition
    upstream = Parser(upstream)
    T = upstream.T.m_as('kelvin')
    P = upstream.P.m_as('pascal')
    gas.TP = T, P
    phi = upstream.phi.m
    gas.set_equivalence_ratio(phi, upstream.fuel, upstream.oxidizer)

    # set up flame object
    width = Parser(domain).width.m_as('meter')
    f = ct.FreeFlame(gas, width=width)
    f.set_refine_criteria(ratio=3, slope=0.06, curve=0.12)
    if loglevel > 0:
        f.show_solution()

    out = {}

    # Solve with mixture-averaged transport model
    f.transport_model = 'Mix'
    f.solve(loglevel=loglevel, auto=True)

    # Solve with the energy equation enabled
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: mixture-averaged flamespeed = {1:7f} m/s'
    print(msg.format(name, f.velocity[0]))

    group = name + "<mix>"
    out[group] = f

    # Solve with multi-component transport properties
    f.transport_model = 'Multi'
    f.solve(loglevel)  # don't use 'auto' on subsequent solves
    if loglevel > 0:
        f.show_solution()
    msg = '    {0:s}: multi-component flamespeed  = {1:7f} m/s'
    print(msg.format(name, f.velocity[0]))

    group = name + "<multi>"
    out[group] = f

    return out


def save(data: Dict[str, Any], output: Optional[Dict[str, Any]] = None,
         mode: Optional[str] = 'a') -> None:
    """
    This function saves the output from the run method

    Arguments:
        data: data to be saved
        output: naming information
        mode: append or write. default to append
    """

    if output is None:
        return

    oname = output['file_name']
    opath = output['path']
    formatt = output['format']
    force = output['force_overwrite']

    if oname is None:
        return
    if opath is not None:
        oname = os.path.join(opath, oname)

    # file check
    fexists = os.path.isfile(oname)

    if not fexists and mode == 'a':
        mode = 'w'
    if fexists and mode == 'w' and not force:
        msg = 'Cannot overwrite existing file `{}` (use force to override)'
        raise RuntimeError(msg.format(oname))

    if fexists:
        with h5py.File(oname, 'r') as hdf:
            groups = {k: 'Group' for k in hdf.keys()}
    else:
        groups = {}

    for key in data:
        if formatt in {'h5', 'hdf5', 'hdf'}:
            if key in groups and mode == 'a' and not force:
                msg = 'Cannot overwrite existing group `{}` (use force to override)'
                raise RuntimeError(msg.format(key))
            data[key].write_hdf(oname, group=key, mode=mode)
        else:
            raise ValueError("Invalid file format {}".format(formatt))

        mode = 'a'


if __name__ == "__main__":
    config = defaults()
    df = run('main', **config, loglevel=1)
    save(df)
