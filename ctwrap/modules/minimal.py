"""Minimal example for ctwrap compatible simulation module"""

import time

from ruamel import yaml

__DEFAULTS = """\
# default parameters for the `minimal` module
sleep: 0.2
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name, sleep=.2):
    """This function does nothing"""

    # initialize
    print('    - `minimal`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)

    return {name: {'sleep': [sleep]}}


def save(data, output=None, mode='a') :
    """this function does nothing"""

    return


if __name__ == "__main__":

    config = defaults()
    out = run('main', **config)
    save(out)
