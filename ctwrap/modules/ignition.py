""" Module to run ignition simulation """
import os
import warnings
from typing import Optional, Dict, Any
from ruamel import yaml
import h5py


from ctwrap import Parser


try:
    import cantera as ct
except ImportError as err:
    warnings.warn(
        "This module will not work without an installation of Cantera",
        UserWarning)

# default configuration
__DEFAULTS = """\
# default parameters for the `ignition` module
initial:
  T: [1000., kelvin, 'temperature']
  P: [1., atmosphere, 'pressure']
  phi: [1., dimensionless, 'equivalence ratio']
  fuel: 'H2'
  oxidizer: 'O2:1.,AR:3.76'
chemistry:
  mechanism: h2o2.xml
simulation:
  delta_t: 1.e-5
  n_points: 500
  atol: 1.e-15
  rtol: 1.e-9
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name: str,
        chemistry: Optional[Dict[str, Any]] = None,
        initial: Optional[Dict[str, Any]] = None,
        simulation: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
    """
    Function handling reactor simulation.
    The function uses the class 'ctwrap.Parser' in conjunction with 'pint.Quantity'
    for handling and conversion of units.

    Arguments:
        name (str): name of the task
        chemistry  (dict): reflects yaml 'configuration:chemistry'
        initial    (dict): reflects yaml 'configuration:initial'
        simulation (dict): reflects yaml 'configuration:simulation'

    Returns:
        Dictionary containing Cantera SolutionArray
    """

    # initialize

    # gas object
    mech = Parser(chemistry).mechanism
    gas = ct.Solution(mech)

    # temperature, pressure, and composition
    initial = Parser(initial)
    T = initial.T.m_as('kelvin')
    P = initial.P.m_as('pascal')
    gas.TP = T, P
    phi = initial.phi.m
    gas.set_equivalence_ratio(phi, initial.fuel, initial.oxidizer)

    # define a reactor network
    reactor = ct.IdealGasConstPressureReactor(gas)
    sim = ct.ReactorNet([reactor])

    # set simulation parameters
    par = Parser(simulation)
    sim.atol = par.atol
    sim.rtol = par.rtol
    delta_t = par.delta_t
    n_points = par.n_points

    # SolutionArray
    states = ct.SolutionArray(gas, extra=['t'])

    # Run simulation
    time = sim.time

    # loop: note that advance() returns boolean
    for i in range(n_points):

        time += delta_t
        sim.advance(time)

        states.append(reactor.thermo.state, t=time)

    out = {}
    out[name] = states

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

    # file check
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


###

if __name__ == "__main__":
    config = defaults()
    out = run('main', **config)
    save(out)
