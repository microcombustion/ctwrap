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

    def test_basic(self):

        values = [0, 1, 2, 3]
        specs = {'foobar': values}
        seq = cw.Strategy.load(sequence=specs)
        self.assertIsInstance(seq, cw.Sequence)

        defaults = {'foobar': 1, 'spam': 2.0, 'eggs': 3.14}
        tasks = seq.create_tasks(defaults)
        task_keys = list(tasks.keys())

        for i, val in enumerate(values):
            self.assertEqual(val, tasks[task_keys[i]]['foobar'])

    def test_invald(self):

        specs = {'foo': [0, 1, 2], 'bar': [3, 4]}
        with self.assertRaisesRegex(TypeError, "Strategy needs"):
            cw.Strategy.load(sequence=specs['foo'])

        with self.assertRaisesRegex(ValueError, "Invalid length"):
            cw.Strategy.load(sequence=specs)

        specs.pop('foo')
        with self.assertRaisesRegex(ValueError, "Invalid length"):
            cw.Strategy.load(matrix=specs)

    def test_unknown(self):

        specs = {'foo': [0, 1, 2], 'bar': [3, 4]}
        with self.assertRaisesRegex(NotImplementedError, "Unknown strategy"):
            cw.Strategy.load(foobar=specs)

    def test_minimal(self):

        mm = cw.Parser.from_yaml('minimal.yaml', path=EXAMPLES)
        strategy = mm.strategy.raw
        seq = cw.Strategy.load(**strategy)
        self.assertEqual(seq.sweep['sleep'], strategy['sequence']['sleep'])

    def test_legacy(self):

        mm = cw.Parser.from_yaml('legacy.yaml', path=EXAMPLES)
        seq = cw.Sequence.from_legacy(mm.variation.raw)
        self.assertEqual(seq.sweep['initial.phi'], mm.variation.raw['values'])

    def test_matrix(self):

        specs = {'foo': [0, 1, 2], 'bar': [3, 4]}
        defaults = {'foo': None, 'bar': None}
        mat = cw.Strategy.load(matrix=specs)
        self.assertIsInstance(mat, cw.Matrix)
        tasks = mat.create_tasks(defaults)
        self.assertEqual(len(tasks), 6)
