#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ignition reactor executable"""

from __future__ import division, absolute_import, print_function, unicode_literals

import argparse
import os
import ctwrap

import warnings
warnings.filterwarnings(action='once')
#warnings.filterwarnings("ignore", ".*Using or importing the ABCs from *")
#warnings.filterwarnings("ignore", ".*html argument of XMLParser() *")
warnings.filterwarnings("ignore",
                        "object name is not a valid Python identifier:")


def main():
    """Main."""

    # set up argument parser
    parser = argparse.ArgumentParser(
        description='Simulation of adiabatic flames (ctwrap).')
    parser.add_argument('config', help='yaml configuration file')
    parser.add_argument('--path', help='path to configuration', default='.')
    parser.add_argument('--output', help='name of output file')
    # parser.add_argument(
    #     '-p',
    #     '--processes',
    #     action='count',
    #     help='number of parallel processes',
    #     default=0)
    parser.add_argument(
        '-v', '--verbosity', action='count', default=1, help='verbosity level')
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=False,
        help='run parallel calculations')

    # parse arguments
    args = parser.parse_args()
    yml_file = args.config
    path = args.path
    verbosity = args.verbosity
    parallel = args.parallel
    if args.output is None:
        output_file = None
    else:
        output_file = args.output

    # verbose output
    if verbosity:
        print(60 * '#')
        print('Freely propagating adiabatic flame (ctwrap)')
        print(60 * '#')
        msg = 'Conditions specified in `{}` '
        print(msg.format(yml_file))  # , end='')

    # set up variation
    sim = ctwrap.Simulation.from_module(ctwrap.modules.adiabatic_flame)
    reactor = ctwrap.SimulationHandler.from_yaml(
        yml_file,
        path=path,
        verbosity=verbosity,
        oname=output_file,
        opath=path)

    # run parameter variation
    if parallel:
        reactor.run_parallel(sim)
    else:
        reactor.run_serial(sim)
