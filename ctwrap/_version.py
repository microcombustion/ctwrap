#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Versioning information/credits

https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-your-project-s-version
"""

__version_info__ = (0, 1, 0)
__version__ = '.'.join(map(str, __version_info__[:3]))
if len(__version_info__) == 4:
    __version__ += __version_info__[-1]
