#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import subprocess
import importlib
import h5py
from ruamel.yaml import YAML

import warnings
# add exception as pywintypes imports a deprecated module
warnings.filterwarnings("ignore", ".*the imp module is deprecated*")

# pylint: disable=import-error
import ctwrap as cw


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'ctwrap' / 'yaml'


class TestLegacy(unittest.TestCase):

    def test_handler(self):
        with self.assertWarnsRegex(PendingDeprecationWarning, "Old implementation"):
            sh = cw.SimulationHandler.from_yaml('legacy.yaml', database=EXAMPLES)
        self.assertIsInstance(sh.tasks, dict)

    def test_database(self):
        with self.assertWarnsRegex(PendingDeprecationWarning, "Old implementation"):
            sh = cw.SimulationHandler.from_yaml('legacy.yaml')
        self.assertIsInstance(sh.tasks, dict)


class TestWrap(unittest.TestCase):

    _module = cw.modules.minimal
    _yaml = 'minimal.yaml'
    _out = None
    _path = None
    _parser = False
    _strategy = 'sequence'
    _data_default = 'dict'
    _skip_long = False

    def setUp(self):
        with open(EXAMPLES / self._yaml) as stream:
            yaml = YAML(typ='safe')
            self.config = yaml.load(stream)
        self.sim = cw.Simulation.from_module(self._module)
        self.sh = cw.SimulationHandler.from_yaml(self._yaml, strategy=self._strategy, database=EXAMPLES)

    def tearDown(self):
        if self._out:
            [out.unlink() for out in Path(EXAMPLES).glob('*.h5')]
            [out.unlink() for out in Path(ROOT).glob('*.h5')]
            [out.unlink() for out in Path(ROOT).glob('*.csv')]

    def test_simulation(self):
        self.assertIsNone(self.sim.data)
        defaults = self.config['defaults']
        if self._parser:
            self.sim.run(cw.Parser(defaults))
        else:
            self.sim.run(defaults)
        self.assertEqual(type(self.sim.data).__name__, self._data_default)

    def test_restart(self):
        defaults = self.config['defaults']
        if self._parser:
            self.sim.run(cw.Parser(defaults))
        else:
            self.sim.run(defaults)
        self.sim.run()
        old = self.sim.data
        if self.sim.has_restart:
            self.sim.restart(old)
            new = self.sim.data
            self.assertEqual(type(old), type(new))
            #self.assertNotEqual(old, new)
        else:
            with self.assertRaisesRegex(NotImplementedError, "does not define 'restart'"):
                self.sim.restart(old)

    def test_handler(self):
        self.assertIsInstance(self.sh.tasks, dict)

    def test_serial(self):
        if self._skip_long:
            return
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
        if self._skip_long:
            return
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
    _yaml = 'ignition.yaml'
    _out = 'ignition.h5'
    _parser = True
    _strategy = None
    _data_default = 'SolutionArray'
    _skip_long = True


class TestSolution(TestWrap):

    _module = cw.modules.solution
    _yaml = 'solution.yaml'
    _out = 'solution.csv'
    _parser = True
    _strategy = None
    _data_default = 'Solution'


class TestEquilibrium(TestWrap):

    _module = cw.modules.equilibrium
    _yaml = 'equilibrium.yaml'
    _out = 'equilibrium.csv'
    _parser = True
    _strategy = None
    _data_default = 'Solution'


class TestEquilibriumMulti(TestEquilibrium):

    _yaml = 'equilibrium_multi.yaml'
    _out = 'equilibrium_multi.csv'
    _data_default = 'Mixture'


class TestFreeFlame(TestWrap):

    _module = cw.modules.freeflame
    _yaml = 'freeflame.yaml'
    _out = 'freeflame.h5'
    _parser = True
    _strategy = 'sequence'
    _data_default = 'FreeFlame'


class TestFreeFlameMatrix(TestFreeFlame):

    _module = cw.modules.freeflame
    _yaml = 'freeflame.yaml'
    _out = 'freeflame.h5'
    _strategy = 'matrix'
    _skip_long = True


class TestInvalid(TestWrap):

    _module = str(ROOT / 'tests' / 'invalid.py')
    _dict = {
        'strategy': {'sequence': {'foo': [0, 1, 2]}},
        'defaults': {'foo': None},
        'output': {'name': 'invalid', 'format': 'h5'},
        'ctwrap': '0.3.0'
    }

    def setUp(self):
        with open(EXAMPLES / self._yaml) as stream:
            yaml = YAML(typ='safe')
            self.config = yaml.load(stream)
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
        with self.assertRaisesRegex(RuntimeError, "Hello world!"):
            super().test_simulation()

    def test_restart(self):
        with self.assertRaisesRegex(RuntimeError, "Hello world!"):
           super().test_restart()

    def test_serial(self):
        with self.assertWarnsRegex(RuntimeWarning, "Hello world!"):
            super().test_serial()

    def test_parallel(self):
        with self.assertWarnsRegex(RuntimeWarning, "unable to open file"):
            super().test_parallel()

    def test_main(self):
        # skip test (does not use setUp and is more involved)
        pass

    def test_commandline(self):
        # skip test (does not use setUp and is more involved)
        pass


if __name__ == "__main__":
    unittest.main()
