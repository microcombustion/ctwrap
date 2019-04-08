#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Template demonstrating """

import pandas as pd
import time

from ctwrap.fileio import load_yaml


def template(name, sleep=.2, **kwargs):
    """this function does nothing"""

    # initialize
    print('    - `template`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)

    return {name: pd.DataFrame({'sleep': [sleep]})}


if __name__ == "__main__":

    config = load_yaml('template.yaml')
    template('main', **config)
