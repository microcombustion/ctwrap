"""Simulation module illustrating a minimal ctwrap example
Note: the ``save`` method is skipped
"""
import time


def defaults():
    """Returns dictionary containing default arguments"""
    return {'foo': 0.2, 'bar': 1}


def run(name, foo=.2, bar=1):
    """This method 'sleeps' for the specified duration"""
    msg = '    - `minimal`: sleeping for {} * {} = {} seconds ...'
    print(msg.format(foo, bar, foo * bar))
    time.sleep(foo * bar)
    return {name: {'sleep': [foo * bar]}}


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
