#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

# get version
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'ctwrap', '_version.py')) as version_file:
    exec(version_file.read())


""" load readme """
with open('README.md', 'r', encoding="utf-8") as f:
    long_description = f.read()

# configuration
setup(
    name='ctwrap',
    version=__version__,
    description='Python wrapper for batch simulations',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.6',
    keywords='python, wrapper, cantera',
    url='https://github.com/microcombustion/ctwrap',
    author=__author__,
    author_email='ischoegl@lsu.edu',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['ctwrap=ctwrap.bin.ctwrap:main'],
    },
    include_package_data=True,
    install_requires=[
        'h5py', 'numpy', 'pandas', 'pint', 'ruamel.yaml'],
    zip_safe=False
)
