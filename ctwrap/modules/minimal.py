"""Simulation module illustrating minimal ctwrap example"""
import time


def defaults():
    """Returns dictionary containing default arguments"""
    return {'sleep': 0.2}


def run(name, sleep=.2):
    """This method 'sleeps' for the specified duration"""
    print('    - `minimal`: sleeping for {} seconds ...'.format(sleep))
    time.sleep(sleep)
    return {name: {'sleep': [sleep]}}


def save(data, output=None, mode='a') :
    """This method is required by ctwrap (but does nothing in this example)"""
    return


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run('main', **config)
