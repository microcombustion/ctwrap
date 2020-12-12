#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import pint.quantity as pq

import ctwrap as cw


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = '{}'.format(ROOT / 'yaml')


class TestParse(unittest.TestCase):

    def test_string(self):

        value, unit = cw.parse('hello world')
        self.assertEqual(value, 'hello world')
        self.assertIsNone(unit)

    def test_full(self):

        value, unit = cw.parse('1 spam')
        self.assertEqual(value, '1')
        self.assertEqual(unit, 'spam')

    def test_no_unit(self):

        value, unit = cw.parse('2.')
        self.assertEqual(value, '2.')
        self.assertEqual(unit, 'dimensionless')


class TestWrite(unittest.TestCase):

    def test_string(self):

        value = cw.write('hello world')
        self.assertEqual(value, 'hello world')

    def test_full(self):

        value = cw.write(1, 'spam')
        self.assertEqual(value, '1 spam')

    def test_no_unit1(self):

        value = cw.write(2., None)
        self.assertEqual(value, '2.0')

    def test_no_unit2(self):

        value = cw.write(2., 'dimensionless')
        self.assertEqual(value, '2.0')


class TestParser(unittest.TestCase):

    def test_ignition(self):

        defaults = cw.parser.load_yaml(
            'ignition.yaml', path=EXAMPLES, keys=['defaults'])
        p = cw.Parser(defaults[0]['initial'])
        self.assertIsInstance(p.T, pq.Quantity)
        self.assertIsInstance(p.T.m, float)
        self.assertEqual(str(p.T.units), 'kelvin')
        self.assertEqual(p.T.m - 273.15, p.T.m_as('degC'))
        self.assertIsInstance(p.fuel, str)

    def test_adiabatic_flame(self):

        defaults = cw.parser.load_yaml(
            'adiabatic_flame.yaml', path=EXAMPLES, keys=['defaults'])
        p = cw.Parser(defaults[0]['upstream'])
        self.assertIsInstance(p.T, pq.Quantity)
        self.assertIsInstance(p.T.m, float)
        self.assertEqual(str(p.T.units), 'kelvin')
        self.assertEqual(p.T.m - 273.15, p.T.m_as('degC'))
        self.assertIsInstance(p.fuel, str)
