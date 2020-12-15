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
from ctwrap.strategy import _replace_entry, _sweep_matrix, _task_list


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

    def test_one(self):
        dd = {'foo': [1, 2, 3, 4]}
        out = _task_list(dd)
        self.assertEqual(len(out), 4)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 4)
        self.check(dict(zip(out, configs)))

    def test_two(self):
        dd = {'foo': [1, 2, 3, 4], 'bar': [5, 6, 7]}
        out = _task_list(dd)
        self.assertEqual(len(out), 12)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 12)
        self.check(dict(zip(out, configs)))

    def test_three(self):
        dd = {'foo': [1, 2, 3, 4], 'bar': [5, 6, 7], 'baz': [8, 9]}
        out = _task_list(dd)
        self.assertEqual(len(out), 24)
        configs = _sweep_matrix(dd, self._default)
        self.assertEqual(len(configs), 24)
        self.check(dict(zip(out, configs)))


class TestStrategy(unittest.TestCase):

    _specs_one = {'foobar': range(4)}
    _specs_two = {'foo': [0, 1, 2], 'bar': [3, 4]}

    def test_load(self):

        seq = cw.Strategy.load({'sequence': self._specs_one})
        self.assertIsInstance(seq, cw.Sequence)

        seq = cw.Strategy.load({'sequence_test': self._specs_one})
        self.assertIsInstance(seq, cw.Sequence)

        seq = cw.Strategy.load({'my_sequence': self._specs_one})
        self.assertIsInstance(seq, cw.Sequence)

        seq = cw.Strategy.load({'my_sequence_test': self._specs_one})
        self.assertIsInstance(seq, cw.Sequence)

        seq = cw.Strategy.load({'my_sequence_test': self._specs_one})
        self.assertIsInstance(seq, cw.Sequence)

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
        tasks = seq.create_tasks(defaults)
        task_keys = list(tasks.keys())

        values = self._specs_one['foobar']
        for i, val in enumerate(values):
            self.assertEqual(val, tasks[task_keys[i]]['foobar'])

    def test_matrix(self):

        mat = cw.Matrix(self._specs_two)
        defaults = {'foo': None, 'bar': None, 'baz': 3.14}
        tasks = mat.create_tasks(defaults)
        self.assertEqual(len(tasks), 6)

    def test_minimal(self):

        mm = cw.Parser.from_yaml('minimal.yaml', path=EXAMPLES)
        strategy = mm.strategy.raw
        seq = cw.Strategy.load(strategy, name='sequence')
        self.assertEqual(seq.sweep, strategy['sequence'])

        mat = cw.Strategy.load(strategy, name='matrix')
        self.assertEqual(mat.matrix, strategy['matrix'])

    def test_legacy(self):

        mm = cw.Parser.from_yaml('legacy.yaml', path=EXAMPLES)
        seq = cw.Sequence.from_legacy(mm.variation.raw)
        self.assertEqual(seq.sweep['initial.phi'], mm.variation.raw['values'])
