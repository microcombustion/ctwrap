#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import pint.quantity as pq
from ruamel import yaml

import ctwrap as cw
from ctwrap.parser import _parse as parse
from ctwrap.parser import _write as write


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'yaml'


class TestParse(unittest.TestCase):

    def test_string(self):

        value, unit = parse('hello world')
        self.assertEqual(value, 'hello world')
        self.assertIsNone(unit)

    def test_full(self):

        value, unit = parse('1 spam')
        self.assertEqual(value, '1')
        self.assertEqual(unit, 'spam')

    def test_no_unit1(self):

        value, unit = parse('2.')
        self.assertEqual(value, '2.')
        self.assertIsNone(unit)

    def test_no_unit2(self):

        value, unit = parse('2. ')
        self.assertEqual(value, '2.')
        self.assertEqual(unit, 'dimensionless')


class TestWrite(unittest.TestCase):

    def test_string(self):

        value = write('hello world')
        self.assertEqual(value, 'hello world')

    def test_full(self):

        value = write(1, 'spam')
        self.assertEqual(value, '1 spam')

    def test_no_unit1(self):

        value = write(2., None)
        self.assertEqual(value, '2.0')

    def test_no_unit2(self):

        value = write(2., 'dimensionless')
        self.assertEqual(value, '2.0')


class TestParser(unittest.TestCase):

    def test_minimal(self):

        with open(EXAMPLES / 'minimal.yaml') as stream:
            defaults = yaml.load(stream, Loader=yaml.SafeLoader)
        p = cw.Parser.from_yaml('minimal.yaml', path=EXAMPLES)
        self.assertEqual(len(p), len(defaults))
        self.assertEqual(p.keys(), defaults.keys())
        self.assertIn('defaults', p)
        dd1 = {**p}
        self.assertIsInstance(dd1['defaults'], cw.Parser)
        dd2 = {key: val for key, val in p.items()}
        self.assertEqual(dd1.keys(), dd2.keys())

    def test_ignition(self):

        with open(EXAMPLES / 'ignition.yaml') as stream:
            yml = yaml.load(stream, Loader=yaml.SafeLoader)
        initial = yml['defaults']['initial']
        self.assertIsInstance(initial['T'], float)
        self.assertIsInstance(initial['fuel'], str)

    def test_adiabatic_flame(self):

        parser = cw.Parser.from_yaml(
            'adiabatic_flame.yaml', path=EXAMPLES, keys=['defaults'])
        up = parser.defaults.upstream
        self.assertIsInstance(up.T, pq.Quantity)
        self.assertIsInstance(up.T.m, float)
        self.assertEqual(str(up.T.units), 'kelvin')
        self.assertEqual(up.T.m - 273.15, up.T.m_as('degC'))
        self.assertIsInstance(up.fuel, str)
