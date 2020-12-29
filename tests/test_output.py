#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import pytest
import unittest
from pathlib import Path
import h5py
from ruamel import yaml

import warnings
# add exception as pywintypes imports a deprecated module
warnings.filterwarnings("ignore", ".*the imp module is deprecated*")

# pylint: disable=import-error
# pylint: disable=no-member
import ctwrap.output as cwo

import pkg_resources

# avoid explicit dependence on cantera
try:
    pkg_resources.get_distribution('cantera')
except pkg_resources.DistributionNotFound:
    ct = ImportError('Method requires a working cantera installation.')
else:
    import cantera as ct


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'yaml'


class TestOutput(unittest.TestCase):

    _yaml = 'minimal.yaml'
    _config = None
    _out = None

    @classmethod
    def setUpClass(cls):
        with open(EXAMPLES / cls._yaml) as stream:
            cls._config = yaml.load(stream, Loader=yaml.SafeLoader)

        out = cls._config.get('output')
        if out:
            cls._output = cwo.Output.from_dict(
                out, file_name=cls._out, file_path=PWD
            )
        else:
            cls._output = None

    def tearDown(self):
        if not self._output:
            return

        fname = Path(self._output.output_name)
        if fname.is_file():
            fname.unlink()

    def test_output(self):
        if not self._output:
            return

        self.assertIsInstance(self._output, cwo.Output)
        self.assertEqual(self._output.settings['name'], self._out)

    def test_dir(self):
        if self._out:
            self.assertEqual(set(self._output.dir()), {'foo', 'bar'})


class TestCSV(TestOutput):

    def test_csv(self):
        if not self._output:
            return

        self.assertIsInstance(self._output, cwo.WriteCSV)
        self.assertEqual(self._output.settings['format'], 'csv')


@pytest.mark.skipif(isinstance(ct, ImportError), reason="Cantera not installed")
class TestSolution(TestCSV):

    _yaml = 'equilibrium.yaml'
    _out = 'solution.csv'

    def setUp(self):
        self._gas = ct.Solution('h2o2.yaml')
        self._output.save(self._gas, 'foo')
        self._gas.TP = 500, ct.one_atm
        self._output.save(self._gas, 'bar')

    def test_add(self):
        self._gas.TP = 700, ct.one_atm
        self._output.save(self._gas, 'spam', variation={'eggs': 1.})
        self.assertEqual(self._output.dir(), ['foo', 'bar', 'spam'])


@pytest.mark.skipif(isinstance(ct, ImportError), reason="Cantera not installed")
class TestMixture(TestCSV):

    _yaml = 'equilibrium_multi.yaml'
    _out = 'mixture.csv'

    def setUp(self):
        self._gas = ct.Solution('h2o2.yaml')
        self._carbon = ct.Solution('graphite.yaml')
        self._mix = ct.Mixture([self._gas, self._carbon])
        self._output.save(self._mix, 'foo')
        self._mix.T = 500
        self._output.save(self._mix, 'bar')

    def test_add(self):
        self._mix.T = 700
        self._output.save(self._mix, 'spam', variation={'eggs': 1.})
        self.assertEqual(self._output.dir(), ['foo', 'bar', 'spam'])


class TestHDF(TestOutput):

    def test_hdf(self):
        if not self._output:
            return

        self.assertIsInstance(self._output, cwo.WriteHDF)
        self.assertEqual(self._output.settings['format'], 'h5')


@pytest.mark.skipif(isinstance(ct, ImportError), reason="Cantera not installed")
class TestSolutionArray(TestHDF):

    _yaml = 'ignition.yaml'
    _out = 'solutionarray.h5'

    def setUp(self):
        self._gas = ct.Solution('h2o2.yaml')
        self._arr = ct.SolutionArray(self._gas, 2)
        self._arr.TP = 300., ct.one_atm
        self._output.save(self._arr, 'foo')
        self._arr.TP = 500., ct.one_atm
        self._output.save(self._arr, 'bar')

    def test_load_like(self):
        baz = self._output.load_like('foo', self._arr)
        self.assertEqual(baz.T[0], 300.)


@pytest.mark.skipif(isinstance(ct, ImportError), reason="Cantera not installed")
class TestFreeFlame(TestOutput):

    _yaml = 'freeflame.yaml'
    _out = 'freeflame.h5'

    def setUp(self):
        self._gas = ct.Solution('h2o2.yaml')
        self._gas.TP = 300., ct.one_atm
        f = ct.FreeFlame(self._gas)
        self._output.save(f, 'foo')
        self._gas.TP = 500., ct.one_atm
        self._freeflame = ct.FreeFlame(self._gas)
        self._output.save(self._freeflame, 'bar')

    def test_load_like(self):
        baz = self._output.load_like('foo', self._freeflame)
        self.assertEqual(baz.T[0], 300.)
