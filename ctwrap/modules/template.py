#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Template demonstrating """

from ruamel import yaml
import pandas as pd
import time


__DEFAULTS = """\
# default parameters for the `template` module
sleep: 0.2
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name, sleep=.2, **kwargs):
    """this function does nothing"""

    # initialize
    print('    - `template`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)

    return {name: pd.DataFrame({'sleep': [sleep]})}


if __name__ == "__main__":

    config = defaults()
    run('main', **config)
