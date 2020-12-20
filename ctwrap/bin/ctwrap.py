#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ctwrap executable"""

import argparse
import ctwrap
from pathlib import Path
import importlib

import warnings
warnings.filterwarnings(action='once')
# pylint: disable=no-member

# set up argument parser
parser = argparse.ArgumentParser(
    description='Wrapper for batch simulations (ctwrap).')
parser.add_argument(
    'module_name',
    help='name of wrapped simulation module'
)
parser.add_argument('yaml_config', help='yaml configuration file')
parser.add_argument('--output', help='name of output file')
parser.add_argument(
    '-v', '--verbosity', action='count', default=0, help='verbosity level')
parser.add_argument(
    '--parallel',
    action='store_true',
    default=False,
    help='run parallel calculations')
parser.add_argument(
    '--strategy',
    choices=['sequence', 'matrix'],
    default=None,
    help='batch job strategy')


def main():
    """Main."""

    # parse arguments
    args = parser.parse_args()
    module_name = args.module_name
    yml_file = args.yaml_config
    verbosity = args.verbosity
    parallel = args.parallel
    strategy = args.strategy
    if args.output is None:
        output_file = None
    else:
        output_file = args.output

    # import module
    if (Path.cwd() / module_name).is_file():
        module = module_name
    elif '.' not in module_name:
        module_name = 'ctwrap.modules.' + module_name
        module = importlib.import_module(module_name)
    else:
        module = importlib.import_module(module_name)

    # verbose output
    if verbosity:
        print(80 * '#')
        print('Running simulations: module `{}`'.format(module_name))
        msg = 'Conditions specified in `{}` '
        print(msg.format(yml_file))  # , end='')
        print(80 * '#')

    # set up variation
    sim = ctwrap.Simulation.from_module(module)
    sh = ctwrap.SimulationHandler.from_yaml(
        yml_file, strategy=strategy, verbosity=verbosity, name=output_file)

    # run parameter variation
    if parallel:
        sh.run_parallel(sim)
    else:
        sh.run_serial(sim)

if __name__ == '__main__':
    main()
