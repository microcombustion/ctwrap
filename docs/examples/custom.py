"""Copy of minimal.py"""
import time


def defaults():
    """Returns dictionary containing default arguments"""
    return {'sleep': 0.2}


def run(name, sleep=.2):
    """This method 'sleeps' for the specified duration"""
    print('    - `minimal`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)
    return {name: {'sleep': [sleep]}}


def save(filename, data, task=None):
    """Does nothing for this example"""
    pass


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
