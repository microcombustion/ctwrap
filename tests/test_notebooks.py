"""unit tests to ensure jupyter notebooks run

Testing for the notebooks - use nbconvert to execute all cells of the
notebook.

Based on https://gist.github.com/lheagy/f216db7220713329eb3fc1c2cd3c7826
"""

import unittest
import subprocess
import warnings

from pathlib import Path

ROOT = Path(__file__).parents[1]
NB_DIR = ROOT / 'docs' / 'examples'
YAML_DIR = ROOT / 'ctwrap' / 'yaml'

warnings.filterwarnings(action='error')
warnings.filterwarnings("ignore", ".*inconsistent pixels*")


def get(nbname, nbpath):

    # use nbconvert to execute the notebook
    def test_func(self):
        print('\n--------------- Testing {0} ---------------'.format(nbname))
        print('   {0}'.format(nbpath))
        # execute the notebook using nbconvert to generate html
        nbexe = subprocess.Popen(['jupyter', 'nbconvert', '--to', 'html',
                                  '{0}'.format(nbpath),
                                  '--execute',
                                  '--ExecutePreprocessor.timeout=180'],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        _, err = nbexe.communicate()
        failed = nbexe.returncode
        if failed:
            print('\n <<<<< {0} FAILED >>>>> \n'.format(nbname))
            print('Captured Output: \n\n{0}'.format(err.decode("utf-8")))
        else:
            print('\n ..... {0} Passed ..... \n'.format(nbname))
            # if passed remove the generated html file
            subprocess.call(['rm', str(nbpath.with_suffix('.html'))])

        self.assertFalse(failed)

    return test_func


attrs = dict()

# build test for each notebook
sensor_notebooks = {f.stem: f for f in NB_DIR.glob('*.ipynb')}
for nb in sensor_notebooks:
    attrs['test_'+nb] = get(nb, sensor_notebooks[nb])


class TestPurgeHDF(unittest.TestCase):

    def setUp(self):
        [hdf.unlink() for hdf in Path(YAML_DIR).glob('*.h5')]

    def tearDown(self):
        [hdf.unlink() for hdf in Path(YAML_DIR).glob('*.h5')]


# create class to unit test notebooks
TestNotebooks = type('TestNotebooks', (TestPurgeHDF,), attrs)


if __name__ == '__main__':
    unittest.main()
