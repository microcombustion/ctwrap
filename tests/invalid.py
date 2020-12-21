"""Invalid module - raises error"""


def defaults():
    """Returns dictionary containing default arguments"""
    return {'foo': 0.2}


def run(foo=.2):
    """Simply raise error"""
    raise RuntimeError("Hello world!")


def save(filename, data, task=None):
    """Does nothing for this example"""
    pass


if __name__ == "__main__":
    """ Main function """
    config = defaults()
    out = run(**config)
