#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import pint.quantity as pq
from ruamel import yaml

import warnings
# add exception as pywintypes imports a deprecated module
warnings.filterwarnings("ignore", ".*the imp module is deprecated*")

# pylint: disable=import-error
import ctwrap as cw
from ctwrap.parser import _parse, _write, _update


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'yaml'


class TestUpdate(unittest.TestCase):

    _dict = {'foo': {'spam': 2.0, 'eggs': 3.14}, 'bar': 3, 'baz': 'hello world'}

    def test_level1(self):

        value = 4
        out = _update(self._dict, {'bar': value})
        self.assertEqual(self._dict['foo'], out['foo'])
        self.assertEqual(self._dict['baz'], out['baz'])
        self.assertEqual(out['bar'], value)

    def test_level2(self):

        value = 4
        out = _update(self._dict, {'foo': {'eggs': value}})
        self.assertEqual(self._dict['bar'], out['bar'])
        self.assertEqual(self._dict['foo']['spam'], out['foo']['spam'])
        self.assertEqual(self._dict['baz'], out['baz'])
        self.assertEqual(out['foo']['eggs'], value)

    def test_multi_level(self):

        value1 = 4
        value2 = 5
        out = _update(self._dict, {'foo': {'eggs': value1}, 'bar': value2})
        self.assertEqual(self._dict['foo']['spam'], out['foo']['spam'])
        self.assertEqual(self._dict['baz'], out['baz'])
        self.assertEqual(out['foo']['eggs'], value1)
        self.assertEqual(out['bar'], value2)


class TestParse(unittest.TestCase):

    def test_string(self):

        value, unit = _parse('hello world')
        self.assertEqual(value, 'hello world')
        self.assertIsNone(unit)

    def test_full(self):

        value, unit = _parse('1 spam')
        self.assertEqual(value, '1')
        self.assertEqual(unit, 'spam')

    def test_no_unit1(self):

        value, unit = _parse('2.')
        self.assertEqual(value, '2.')
        self.assertIsNone(unit)

    def test_no_unit2(self):

        value, unit = _parse('2. ')
        self.assertEqual(value, '2.')
        self.assertEqual(unit, 'dimensionless')


class TestWrite(unittest.TestCase):

    def test_string(self):

        value = _write('hello world')
        self.assertEqual(value, 'hello world')

    def test_full(self):

        value = _write(1, 'spam')
        self.assertEqual(value, '1 spam')

    def test_no_unit1(self):

        value = _write(2., None)
        self.assertEqual(value, '2.0')

    def test_no_unit2(self):

        value = _write(2., 'dimensionless')
        self.assertEqual(value, '2.0')


class TestPassing(unittest.TestCase):

    _entry = {'key': 1.}

    def test_parser(self):

        p = cw.Parser(self._entry)
        self.assertEqual(self._entry, p.raw)


class TestKeyStr(TestPassing):

    _entry = {'spam': 'eggs'}


class TestParser(TestPassing):

    _entry = cw.Parser({'key': 1.})

    def test_parser(self):

        p = cw.Parser(self._entry)
        self.assertEqual(self._entry.raw, p.raw)


class TestMulti(TestParser):

    _dict = {'foo': {'spam': 2.0, 'eggs': 3.14}, 'bar': 3, 'baz': '1. kelvin'}
    _entry = cw.Parser(_dict)
    _new = {'foo': {'eggs': 4}, 'bar': 5}

    def check(self, p):

        self.assertEqual(p.foo.spam, self._entry.foo.spam)
        self.assertEqual(p.baz, self._entry.baz)
        self.assertEqual(p.foo.eggs, self._new['foo']['eggs'])
        self.assertEqual(p.bar, self._new['bar'])

    def test_update_dict(self):

        p = cw.Parser(self._dict)
        p.update(self._new)
        self.check(p)

    def test_update_parser(self):

        p = self._entry
        p.update(cw.Parser(self._new))
        self.check(p)


class TestFailing(unittest.TestCase):

    _entry = None

    def test_parser(self):

        with self.assertRaises(TypeError):
            cw.Parser(self._entry)


class TestInt(TestFailing):

    _entry = 1


class TestFloat(TestFailing):

    _entry = 3.14


class TestString(TestFailing):

    _entry = 'hello world'


class TestYAML(unittest.TestCase):

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
        self.assertEqual(dd1['defaults'], dd2['defaults'])

    def test_ignition(self):

        with open(EXAMPLES / 'ignition.yaml') as stream:
            yml = yaml.load(stream, Loader=yaml.SafeLoader)
        initial = cw.Parser(yml['defaults']['initial'])
        self.assertIsInstance(initial.T, pq.Quantity)
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
