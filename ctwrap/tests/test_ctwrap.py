#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""unit tests to ensure essential hyperstack functions
"""

import unittest

import warnings
warnings.filterwarnings(action='once')
warnings.filterwarnings("ignore", ".*Using or importing the ABCs from *")

import os

import numpy as np
import logging

import ctwrap as cw

path = 'ctwrap/tests'


class TestCtwrap(unittest.TestCase):

    def test010_ignition_serial(self):

        try:
            nv = cw.Variation.from_yaml('ignition_test.yaml', path=path)
            nv.run_serial(reactor=cw.Ignition)
            success = True
        except:
            success = False
        return success

    def test020_ignition_parallel(self):

        try:
            nv = cw.Variation.from_yaml('ignition_test.yaml', path=path)
            nv.run_parallel(reactor=cw.Ignition, number_of_processes=2)
            success = True
        except:
            success = False
        return success

    def test030_ignition_xlsx(self):

        try:
            nv = cw.Variation.from_yaml(
                'ignition_test.yaml',
                path=path,
                output='ignition_test.xlsx')
            nv.run_parallel(reactor=cw.Ignition, number_of_processes=2)
            success = True
        except:
            success = False
        return success

    def test030_ignition_csv(self):

        try:
            nv = cw.Variation.from_yaml(
                'ignition_test.yaml',
                path=path,
                output='ignition_csv.xlsx')
            nv.run_parallel(reactor=cw.Ignition, number_of_processes=2)
            success = True
        except:
            success = False
        return success

    def test050_ignition_nonreacting(self):

        try:
            nv = cw.Variation.from_yaml(
                'ignition_test.yaml', path=path, reacting=False)
            nv.run_parallel(reactor=cw.Ignition, number_of_processes=2)
            success = True
        except:
            success = False
        return success


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger("SomeTest.testSomething").setLevel(logging.DEBUG)
    unittest.main()
