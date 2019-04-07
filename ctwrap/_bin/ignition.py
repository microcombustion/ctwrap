#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ignition reactor executable"""

from __future__ import division, absolute_import, print_function, unicode_literals

import argparse
import os
from zerod import Variation, Ignition

import warnings
warnings.filterwarnings(action='once')
warnings.filterwarnings("ignore", ".*Using or importing the ABCs from *")
warnings.filterwarnings("ignore", ".*html argument of XMLParser() *")


def main():
    """Main."""

    # set up argument parser
    parser = argparse.ArgumentParser(
        description='Simulation of constant pressure ignition (zerod).')
    parser.add_argument('config', help='yaml configuration file')
    parser.add_argument('--path', help='path to configuration', default='.')
    parser.add_argument('--output', help='name of output file')
    parser.add_argument(
        '-p',
        '--processes',
        action='count',
        help='number of parallel processes',
        default=0)
    parser.add_argument(
        '-v', '--verbosity', action='count', default=1, help='verbosity level')
    parser.add_argument(
        '--save_species',
        action='store_true',
        default=None,
        help='save species concentrations')

    # parse arguments
    args = parser.parse_args()
    yml_file = args.config
    path = args.path
    processes = max(1, args.processes)
    verbosity = args.verbosity
    save_species = args.save_species
    if args.output is None:
        output_file = yml_file.split('.')
        output_file = '.'.join(output_file[:-1] + ['h5'])
    else:
        output_file = args.output

    # verbose output
    if verbosity:
        print(40 * '#')
        print('Ignition Reactor (zerod)')
        print(40 * '#')
        msg = 'Conditions specified in `{}`: '
        print(msg.format(yml_file), end='')

    # set up variation
    reactor = Variation.from_yaml(
        yml_file,
        path=path,
        verbosity=verbosity,
        output=output_file,
        save_species=save_species)

    # run parameter variation
    if processes == 1:
        reactor.run_serial(reactor=Ignition)
    else:
        reactor.run_parallel(reactor=Ignition, number_of_processes=processes)
