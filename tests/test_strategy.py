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
from ctwrap.strategy import _replace_entry, _sweep_matrix, _task_list, _parse_mode


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = ROOT / 'yaml'


class TestReplace(unittest.TestCase):

    _default = {'foo': {'spam': 2.0, 'eggs': 3.14}, 'bar': 3}

    def test_entry(self):

        value = 4
        out = _replace_entry(self._default, ['bar'], value)
        self.assertEqual(out['foo'], self._default['foo'])
        self.assertEqual(out['bar'], value)

    def test_nested(self):

        value = 5.
        out = _replace_entry(self._default, ['foo', 'spam'], value)
        self.assertEqual(out['foo']['spam'], value)
        self.assertEqual(out['foo']['eggs'], self._default['foo']['eggs'])
        self.assertEqual(out['bar'], self._default['bar'])

    def test_missing1(self):

        value = 6.
        out = _replace_entry(self._default, ['baz'], value)
        self.assertEqual(out, self._default)

    def test_missing2(self):

        value = 6.
        out = _replace_entry(self._default, ['foo', 'ham'], value)
        self.assertEqual(out, self._default)


class TestParse(unittest.TestCase):

    def test_one(self):

        _default = {'test_1': {'limits': [0, 1], 'npoints': 6, 'mode': 'linspace'}}

        value = {'test_1': [0, 0.2, 0.4, 0.6, 0.8, 1.0]}

        out = _parse_mode(_default)

        value_keys, value_list = list(value.items())[0]
        out_keys, out_list = list(out.items())[0]

        self.assertEqual(value_keys, out_keys)
        for i in range(len(value_list)):
            self.assertAlmostEqual(value_list[i], out_list[i])

    def test_two(self):

        _default = {'test_2': {'limits': [0, 1.2], 'step': 0.2, 'mode': 'arange'}}

        value = {'test_2': [0, 0.2, 0.4, 0.6, 0.8, 1.0]}

        out = _parse_mode(_default)

        value_keys, value_list = list(value.items())[0]
        out_keys, out_list = list(out.items())[0]

        self.assertEqual(value_keys, out_keys)
        for i in range(len(value_list)):
            self.assertAlmostEqual(value_list[i], out_list[i])


class TestSweep(unittest.TestCase):

    _default = {'foo': 3, 'bar': 2, 'baz': 1}

    def check(self, task_list):
        print(task_list)
        for task, config in task_list.items():
            items = task.split('_')
            while items:
                key = items.pop(0)
                val = items.pop(0)
                self.assertEqual(str(config[key]), val)

    @staticmethod
    def stringify(items):
        return ['_'.join(['{}_{}'.format(k, v) for k, v in dd.items()]) for dd in items]

    def test_one(self):
        dd = {'foo': [1, 2, 3, 4]}
        out = self.stringify(_task_list(dd))
        self.assertEqual(len(out), 4)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 4)
        self.check(dict(zip(out, configs)))

    def test_two(self):
        dd = {'foo': [1, 2, 3, 4], 'bar': [5, 6, 7]}
        out = self.stringify(_task_list(dd))
        self.assertEqual(len(out), 12)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 12)
        self.check(dict(zip(out, configs)))

    def test_three(self):
        dd = {'foo': [1, 2, 3, 4], 'bar': [5, 6, 7], 'baz': [8, 9]}
        out = self.stringify(_task_list(dd))
        self.assertEqual(len(out), 24)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 24)
        self.check(dict(zip(out, configs)))


class TestStrategy(unittest.TestCase):

    _specs_one = {'foobar': range(4)}
    _specs_two = {'foo': [0, 1, 2], 'bar': [3, 4]}

    def test_load(self):

        for name in ['sequence', 'sequence_test', 'my_sequence', 'my_sequence_test']:

            seq = cw.Strategy.load({name: self._specs_one})
            self.assertIsInstance(seq, cw.Sequence)
            self.assertEqual(seq.name, name)
            self.assertIn(name, seq.definition)
            self.assertIn('foobar', seq.definition[name])

        seq = cw.Strategy.load({'matrix': self._specs_two})
        self.assertIsInstance(seq, cw.Matrix)

        seq = cw.Strategy.load({'sequence': self._specs_one, 'matrix': self._specs_two},
                               name='sequence')
        self.assertIsInstance(seq, cw.Sequence)

        seq = cw.Strategy.load({'sequence': self._specs_one, 'matrix': self._specs_two},
                               name='matrix')
        self.assertIsInstance(seq, cw.Matrix)

    def test_raises(self):

        with self.assertRaisesRegex(TypeError, "Strategy needs"):
            cw.Strategy.load({'sequence': self._specs_two['foo']})

        with self.assertRaisesRegex(ValueError, "Invalid length"):
            cw.Strategy.load({'sequence': self._specs_two})

        with self.assertRaisesRegex(ValueError, "Invalid length"):
            cw.Strategy.load({'matrix': self._specs_one})

        with self.assertRaisesRegex(ValueError, "'name' is required"):
            cw.Strategy.load({'my_sequence_test': self._specs_one, 'matrix': {}})

        with self.assertRaisesRegex(NotImplementedError, "Unknown strategy"):
            cw.Strategy.load({'foobar': self._specs_one})

    def test_sequence(self):

        seq = cw.Sequence(self._specs_one)
        defaults = {'foobar': 1, 'spam': 2.0, 'eggs': 3.14}
        tasks = seq.configurations(defaults)
        task_keys = list(tasks.keys())

        values = self._specs_one['foobar']
        for i, val in enumerate(values):
            self.assertEqual(val, tasks[task_keys[i]]['foobar'])

    def test_matrix(self):

        mat = cw.Matrix(self._specs_two)
        defaults = {'foo': None, 'bar': None, 'baz': 3.14}
        tasks = mat.configurations(defaults)
        self.assertEqual(len(tasks), 6)

    def test_minimal(self):

        mm = cw.Parser.from_yaml('minimal.yaml', path=EXAMPLES)
        strategy = mm.strategy.raw
        seq = cw.Strategy.load(strategy, name='sequence')
        self.assertEqual(seq.sweep, strategy['sequence'])

        mat_output = {'foo': [0.1, 0.2, 0.3], 'bar': [2, 1, 0]}
        mat = cw.Strategy.load(strategy, name='matrix')
        #self.assertEqual(mat.matrix, strategy['matrix'])
        self.assertEqual(mat.matrix, mat_output)

    def test_legacy(self):

        mm = cw.Parser.from_yaml('legacy.yaml', path=EXAMPLES)
        new = cw.Legacy.convert(mm.variation.raw)
        seq = cw.Strategy.load(new)
        self.assertIsInstance(seq, cw.Legacy)
        self.assertEqual(seq.sweep['initial.phi'], mm.variation.raw['values'])
