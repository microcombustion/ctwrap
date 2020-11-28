#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import subprocess
import pint.quantity as pq

import ctwrap as cw


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

    _module = cw.modules.minimal
    _task = 'sleep_0.4'
    _yaml = 'minimal.yaml'
    _hdf = None

    def test_simulation(self):
        sim = cw.Simulation.from_module(self._module)
        self.assertIsNone(sim.data)
        sim.run()
        self.assertIsInstance(sim.data, dict)
        for key in sim.data.keys():
            self.assertIn('defaults', key)

    def test_handler(self):
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertIsInstance(sh.tasks, dict)
        self.assertIn(self._task, sh.tasks)

    def test_serial(self):
        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_serial(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())
            hdf.unlink()

    def test_parallel(self):
        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_parallel(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())
            hdf.unlink()

    def test_commandline(self):
        cmd = 'ctwrap'
        name = self._module.__name__.split('.')[-1]
        yaml = "{}".format(Path(EXAMPLES) / self._yaml)
        pars = [name, yaml, '--parallel']

        self.maxDiff = None
        process = subprocess.Popen([cmd] + pars,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        self.assertEqual(stderr.decode(), '')

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())
            hdf.unlink()


class TestIgnition(TestWrap):

    _module = cw.modules.ignition
    _task = 'initial.phi_0.4'
    _yaml = 'ignition.yaml'
    _hdf = 'ignition.h5'


class TestAdiabaticFlame(TestWrap):

    _module = cw.modules.adiabatic_flame
    _task = 'upstream.phi_0.4'
    _yaml = 'adiabatic_flame.yaml'
    _hdf = 'adiabatic_flame.h5'

    def test_commandline(self):
        # disable until deprecationwarnings are fixed
        pass


if __name__ == "__main__":
    unittest.main()
