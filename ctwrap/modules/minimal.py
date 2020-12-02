"""Minimal example for ctwrap compatible simulation module"""

import time
from typing import Dict, Any, Optional
import pandas as pd

from ruamel import yaml

__DEFAULTS = """\
# default parameters for the `minimal` module
sleep: 0.2
"""


def defaults():
    """Returns dictionary containing default arguments"""
    return yaml.load(__DEFAULTS, Loader=yaml.SafeLoader)


def run(name: str, sleep : Optional[float] = .2) -> Dict[str, Any]:
    """This function does nothing"""

    # initialize
    print('    - `minimal`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)

    return {name: pd.DataFrame({'sleep': [sleep]})}


def save(data: Dict[str, Any], output: Optional[Dict[str, Any]] = None,
         mode: Optional[str] = 'a') -> None:
    """this function does nothing"""

    return


if __name__ == "__main__":

    config = defaults()
    out = run('main', **config)
    save(out)
