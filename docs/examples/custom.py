"""Simple example that shares parameter list with 'minimal.py'"""
import time


def defaults():
    """Returns dictionary containing default arguments"""
    return {'foo': 0.2}


def run(foo=.2, bar=1):
    """This method 'sleeps' for the specified duration"""
    print('    - `minimal`: sleeping for {} seconds ...'.format(foo))
    time.sleep(foo)
    return {'sleep': [foo]}


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
