#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import subprocess
import pint.quantity as pq
import importlib
import h5py

import warnings
# add exception as pywintypes imports a deprecated module
warnings.filterwarnings("ignore", ".*the imp module is deprecated*")

# pylint: disable=import-error
import ctwrap as cw


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'yaml'


class TestLegacy(unittest.TestCase):

    def test_handler(self):
        with self.assertWarnsRegex(PendingDeprecationWarning, "Old implementation"):
            sh = cw.SimulationHandler.from_yaml('legacy.yaml', path=EXAMPLES)
        self.assertIsInstance(sh.tasks, dict)
        self.assertIn('initial.phi_0.4', sh.tasks)


class TestWrap(unittest.TestCase):

    _module = cw.modules.minimal
    _task = 'foo_0.4'
    _yaml = 'minimal.yaml'
    _out = None
    _path = None
    _strategy = 'sequence'

    def setUp(self):
        self.sim = cw.Simulation.from_module(self._module)
        self.sh = cw.SimulationHandler.from_yaml(self._yaml, strategy=self._strategy, path=EXAMPLES)

    def tearDown(self):
        if self._out:
            [out.unlink() for out in Path(EXAMPLES).glob('*.h5')]
            [out.unlink() for out in Path(ROOT).glob('*.h5')]
            [out.unlink() for out in Path(ROOT).glob('*.csv')]

    def test_simulation(self):
        self.assertIsNone(self.sim.data)
        self.sim.run()
        self.assertIsInstance(self.sim.data, dict)
        for key in self.sim.data.keys():
            self.assertIn('unspecified', key)

    def test_handler(self):
        self.assertIsInstance(self.sh.tasks, dict)
        self.assertIn(self._task, self.sh.tasks)

    def test_serial(self):
        self.assertTrue(self.sh.run_serial(self.sim))

        if self._out:
            hdf = Path(EXAMPLES) / self._out
            self.assertTrue(hdf.is_file())

    def test_parallel(self):
        self.assertTrue(self.sh.run_parallel(self.sim))

        if self._out:
            hdf = Path(EXAMPLES) / self._out
            self.assertTrue(hdf.is_file())

    def test_commandline(self):
        cmd = ['ctwrap', 'run']
        if isinstance(self._module, str):
            name = self._module
        else:
            name = self._module.__name__.split('.')[-1]
            if self._path:
                name = str(Path(self._path) / '{}.py'.format(name))
        yaml = str(Path(EXAMPLES) / self._yaml)
        pars = [name, yaml, '--parallel']
        if self._strategy:
            pars += ['--strategy', self._strategy]

        self.maxDiff = None
        process = subprocess.Popen(cmd + pars,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        self.assertEqual(stderr.decode(), '')

        if self._out:
            hdf = Path(EXAMPLES) / self._out
            self.assertTrue(hdf.is_file())

    def test_main(self):

        if isinstance(self._module, str):
            name = self._module
        else:
            name = self._module.__file__

        self.maxDiff = None
        process = subprocess.Popen(['python', name],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        self.assertEqual(stderr.decode(), '')


class TestMatrix(TestWrap):

    _strategy = 'matrix'
    _task ='foo_0.1_bar_0'


class TestLocal(TestWrap):
    # a module in the current folder

    _module = None
    _path = str(PWD.relative_to(Path.cwd()))

    @classmethod
    def setUpClass(cls):
        src = ROOT / 'docs' / 'examples' / 'custom.py'
        dest = PWD / 'custom.py'
        dest.write_text(src.read_text())
        cls._module = importlib.import_module('custom')

    @classmethod
    def tearDownClass(cls):
        (PWD / 'custom.py').unlink()


class TestCustom(TestWrap):

    _module = str(ROOT / 'docs' / 'examples' / 'custom.py')


class TestIgnition(TestWrap):

    _module = cw.modules.ignition
    _task = 'initial.phi_0.4'
    _yaml = 'ignition.yaml'
    _out = 'ignition.h5'
    _strategy = None


class TestEquilibrium(TestWrap):

    _module = cw.modules.equilibrium
    _task = 'initial.phi_0.4'
    _yaml = 'equilibrium.yaml'
    _out = 'equilibrium.csv'
    _strategy = None


class TestAdiabaticFlame(TestWrap):

    _module = cw.modules.adiabatic_flame
    _task = 'upstream.phi_0.4'
    _yaml = 'adiabatic_flame.yaml'
    _out = 'adiabatic_flame.h5'
    _strategy = None


class TestInvalid(TestWrap):

    _module = str(ROOT / 'tests' / 'invalid.py')
    _task = 'foo_1'
    _dict = {
        'strategy': {'sequence': {'foo': [0, 1, 2]}},
        'defaults': {'foo': None},
        'output': {'name': 'invalid', 'format': 'h5'},
        'ctwrap': '0.3.0'
    }

    def setUp(self):
        self.sim = cw.Simulation.from_module(self._module)
        self.sh = cw.SimulationHandler.from_dict(self._dict)

    def tearDown(self):
        h5 = Path('invalid.h5')
        if h5.is_file():
            with h5py.File(h5, 'r') as hdf:
                for data in hdf.values():
                    for attr in data.attrs:
                        self.assertEqual(attr, 'RuntimeError')
                        self.assertEqual(data.attrs[attr], "Hello world!")
            h5.unlink()

    def test_simulation(self):
        with self.assertWarnsRegex(RuntimeWarning, "Hello world!"):
            super().test_simulation()

    def test_serial(self):
        with self.assertWarnsRegex(RuntimeWarning, "Hello world!"):
            super().test_serial()

    def test_main(self):
        # skip test (does not use setUp and is more involved)
        pass

    def test_commandline(self):
        # skip test (does not use setUp and is more involved)
        pass


if __name__ == "__main__":
    unittest.main()
