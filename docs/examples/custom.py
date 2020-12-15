"""Copy of minimal.py"""
import time


def defaults():
    """Returns dictionary containing default arguments"""
    return {'foo': 0.2}


def run(name, foo=.2, bar=1):
    """This method 'sleeps' for the specified duration"""
    print('    - `minimal`: sleeping for {} seconds ...'.format(foo))
    time.sleep(foo)
    return {name: {'sleep': [foo]}}


def save(filename, data, task=None):
    """Does nothing for this example"""
    pass


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
