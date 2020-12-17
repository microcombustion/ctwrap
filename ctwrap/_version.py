"""Versioning information/credits
https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version
"""

__author__ = "I. Schoegl and D. Akinpelu"
__version_info__ = (0, 2, 0)
__version__ = '.'.join(map(str, __version_info__[:3]))
if len(__version_info__) == 4:
    __version__ += __version_info__[-1]
