#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests (just ensures that code does not fail)
"""

import unittest
from pathlib import Path
import subprocess
import pint.quantity as pq

import ctwrap as cw

import warnings
warnings.filterwarnings(action='once')
#warnings.filterwarnings("ignore", ".*Using or importing the ABCs from *")
warnings.filterwarnings("ignore", ".*object name is not a valid Python identifier*")
warnings.filterwarnings("ignore", ".*to be removed after Cantera 2.5*")
warnings.filterwarnings("ignore", ".*Calling the getitem method from a UnitRegistry*")

#warnings.filterwarnings(action='error')

PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = '{}'.format(ROOT / 'examples')


class TestParser(unittest.TestCase):

    def test_parser(self):

        defaults = cw.fileio.load_yaml(
            'ignition.yaml', path=EXAMPLES, keys=['defaults'])
        p = cw.Parser(defaults[0]['initial'])
        self.assertIsInstance(p.T, pq.Quantity)
        self.assertIsInstance(p.T.m, float)
        self.assertEqual(str(p.T.units), 'kelvin')
        self.assertEqual(p.T.m - 273.15, p.T.m_as('degC'))
        self.assertIsInstance(p.fuel, str)


class TestWrap(unittest.TestCase):

    _module = None
    _yaml = None
    _hdf = None

    def test_simulation(self):
        if self._module is None:
            self.assertIsNone(self._yaml)
            return

        sim = cw.Simulation.from_module(self._module)
        self.assertIsNone(sim.data)
        sim.run()
        self.assertIsInstance(sim.data, dict)
        for key in sim.data.keys():
            self.assertIn('defaults', key)

    def test_serial(self):
        if self._module is None:
            self.assertIsNone(self._yaml)
            return

        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_serial(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())
            hdf.unlink()

    def test_parallel(self):
        if self._module is None:
            self.assertIsNone(self._yaml)
            return

        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_parallel(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())
            hdf.unlink()

    def test_commandline(self):
        if self._module is None:
            self.assertIsNone(self._yaml)
            return

        name = self._module.__name__.split('.')[-1]
        cmd = 'ctwrap'
        yaml = Path(EXAMPLES) / self._yaml
        pars = [name, yaml, '--parallel']

        self.maxDiff = None
        process = subprocess.Popen([cmd] + pars,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        self.assertEqual(stderr.decode(), '')


class TestMinimal(TestWrap):

    _module = cw.modules.minimal
    _yaml = 'minimal.yaml'

    def test_handler(self):

        sh = cw.SimulationHandler.from_yaml('minimal.yaml', path=EXAMPLES)
        self.assertIsInstance(sh.tasks, dict)
        self.assertIn('sleep_0.4', sh.tasks)


class TestIgnition(TestWrap):

    _module = cw.modules.ignition
    _yaml = 'ignition.yaml'
    _hdf = 'ignition.h5'


class TestAdiabatic(TestWrap):

    _module = cw.modules.adiabatic_flame
    _yaml = 'adiabatic_flame.yaml'
    _hdf = 'adiabatic_flame.h5'


if __name__ == "__main__":
    unittest.main()
