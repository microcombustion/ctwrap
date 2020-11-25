#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests (just ensures that code does not fail)
"""

import unittest

import warnings
warnings.filterwarnings(action='once')
warnings.filterwarnings("ignore", ".*Using or importing the ABCs from *")

import os

import logging

import ctwrap as cw

path = '../examples/'


class TestCtwrap(unittest.TestCase):
    def test000_parser(self):

        try:
            defaults = cw.fileio.load_yaml(
                'ignition.yaml', path=path, keys=['defaults'])
            p = cw.Parser(defaults[0]['initial'])
            a = p.T  # attribute
            b = p['T']  # get item
            c = p.T.m  # magnitude
            e = p.T.to('degC')  # unit conversion
            d = p.T.m_as('degC')  # magnitude after unit conversion
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test010_minimal(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.minimal)
            sim.run()
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test011_handler(self):

        try:
            sh = cw.SimulationHandler.from_yaml('minimal.yaml', path=path)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test012_minimal_serial(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.minimal)
            sh = cw.SimulationHandler.from_yaml('minimal.yaml', path=path)
            sh.run_serial(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test013_minimal_parallel(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.minimal)
            sh = cw.SimulationHandler.from_yaml('minimal.yaml', path=path)
            sh.run_parallel(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test020_ignition(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.ignition)
            sim.run()
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test021_ignition_serial(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.ignition)
            sh = cw.SimulationHandler.from_yaml('ignition.yaml', path=path)
            sh.run_parallel(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test022_ignition_parallel(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.ignition)
            sh = cw.SimulationHandler.from_yaml('ignition.yaml', path=path)
            sh.run_parallel(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test030_adiabatic_flame(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.adiabatic_flame)
            sim.run()
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test031_adiabatic_flame_serial(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.adiabatic_flame)
            sh = cw.SimulationHandler.from_yaml(
                'adiabatic_flame.yaml', path=path)
            sh.run_serial(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)

    def test032_adiabatic_flame_parallel(self):

        try:
            sim = cw.Simulation.from_module(cw.modules.adiabatic_flame)
            sh = cw.SimulationHandler.from_yaml(
                'adiabatic_flame.yaml', path=path)
            sh.run_parallel(sim)
            success = True
        except:
            success = False

        self.assertTrue(success)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger("SomeTest.testSomething").setLevel(logging.DEBUG)
    unittest.main()
