#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Object handling configurations."""

import os
from pandas import ExcelWriter

__all__ = ['Configuration']


class Configuration(object):
    """Configuration handler.

    Class handles configurations (typically based on dictionary of dictionaries
    loaded from YAML file). 

    Attributes are handled dynamically, where keys of constructor keyword arguments
    are mapped to attributes.
    """

    def __init__(self, verbosity=None, **kwargs):
        """Constructor of configuration handling class.

        Kwargs:
           verbosity (int): verbosity level (ignored)
           plus keywords to be mapped to attributes.
        """

        super(Configuration, self).__init__()

        # parse arguments
        self._config = kwargs.copy()

        # ensure all settings are set
        err = '`{}` not specified'
        for k in self._config.keys():
            assert self._config[k] is not None, err.format(k)

    @property
    def attributes(self):
        """attributes"""
        return list(self._config.keys())

    def __call__(self):
        return self._config

    def __getattr__(self, attr):
        """Access settings dictionary as attribute"""

        assert attr in self._config.keys(), 'invalid attribute'
        return self._config[attr]


class _ReactorBase(Configuration):
    """Rudimentary functions of a reactor"""

    def __init__(self, verbosity=0, **kwargs):
        """Constructor of configuration hanling class.

        Kwargs:
           verbosity (int): verbosity level
           plus keywords to be mapped to attributes.
        """

        super(_ReactorBase, self).__init__(**kwargs)

        self.verbosity = verbosity
        self._dataframe = None

    @property
    def verbose(self):
        return self.verbosity > 0

    def run(self):
        """ stub"""
        if self.verbosity > 0:
            print('Class method `run` needs to be overloaded: do nothing')
        return False

    def save(self, key, oname, path='.'):

        df = self._dataframe
        if df is None:
            return

        save_species = self.output['save_species']
        if isinstance(save_species, tuple):
            keys = [k for k in df.keys() if k not in self.gas.species_names]
            keys += [k for k in save_species]
        elif save_species == True:
            keys = [k for k in df.keys()]
        else:
            keys = [k for k in df.keys() if k not in self.gas.species_names]

        fname = (os.sep).join([path, oname])
        if self.output['format'] in ['hdf', 'h5', 'hdf5']:

            df[keys].to_hdf(fname, key, mode='a', complib='bzip2')
            # complevel=5,

        elif self.output['format'] in ['xlsx']:

            with ExcelWriter(fname, engine='openpyxl', mode='a') as writer:
                df[keys].to_excel(writer, sheet_name=key)

        else:

            raise (NotImplementedError,
                   'output as `.{}` is not implemented'.format(
                       self.output['format']))
