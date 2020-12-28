"""The :py:mod:`output` module defines defines a :class:`Output` object
and derived classes that handle file output for batch jobs of wrapped
:any:`Simulation` module runs.

Class Definitions
+++++++++++++++++
"""

from pathlib import Path
import pandas as pd
import h5py
import json
import warnings

from typing import Dict, List, Any, Optional, Union

import pkg_resources

# avoid explicit dependence on cantera
try:
    pkg_resources.get_distribution('cantera')
except pkg_resources.DistributionNotFound:
    ct = ImportError('Method requires a working cantera installation.')
else:
    import cantera as ct


class Output:
    """Class handling file output

    Arguments:
       settings: Dictionary specifying output settings
       file_name: filename (overrides settings enty)
       file_path: output path (overrides settings entryl)
    """
    _ext = [None]

    def __init__(
            self,
            settings: Dict[str, Any],
            file_name: Optional[str]=None,
            file_path: Optional[str]=None
        ):
        """Constructor"""
        file_format = settings.pop('format', None)
        if isinstance(file_format, str):
            file_format = '.' + file_format.lstrip('.')

        if 'force_overwrite' in settings:
            settings['force'] = settings.pop('force_overwrite')
            warnings.warn("Key 'force_overwrite' is replaced by 'force'",
                          PendingDeprecationWarning)

        if 'file_name' in settings:
            settings['name'] = settings.pop('file_name')
            warnings.warn("Key 'file_name' is replaced by 'name'",
                          PendingDeprecationWarning)

        file_path = settings.pop('path', file_path)
        if file_path is not None:
            file_path = str(file_path)

        # file name keyword overrides dictionary
        if file_name is None:
            file_name = Path(settings.pop('name'))
            if file_format is None:
                file_format = file_name.suffix
            file_name = file_name.stem

        else:
            # file_name may contain path information
            head = Path(file_name).parent
            file_name = Path(file_name).name
            if str(head) != "." and file_path is None:
                file_path = str(head)
            elif str(head) != ".":
                raise RuntimeError('Contradictory path specifications')

            tmp = Path(file_name).suffix
            if tmp:
                file_format = tmp
            file_name = Path(file_name).stem

        # ensure extension matches object type
        if file_format not in self._ext:
            raise ValueError("Incompatible output type for class {}: {} is "
                             "not in {}".format(type(self), file_format, self._ext))

        self.force = settings.pop('force', False)
        self.mode = settings.pop('mode', 'a')
        self.path = file_path
        self.name = file_name + file_format
        self.kwargs = settings.copy()

    @property
    def output_name(self):
        """Return output name"""
        if self.path is None:
            return str(self.name)
        else:
            out = Path(self.path) / self.name
            return str(out)

    @property
    def settings(self):
        """Output settings"""
        out = {
            'format' : Path(self.name).suffix.lstrip('.'),
            'name': self.name,
            'path': self.path,
            'force': self.force,
            'mode': self.mode
        }
        return {**out, **self.kwargs}

    @classmethod
    def from_dict(
            cls,
            settings: Dict[str, Any],
            file_name: Optional[str]=None,
            file_path: Optional[str]=None
        ) -> 'Output':
        """Factory loader for :class:`Output` objects

        Arguments:
           settings: Dictionary containing output settings
        """
        ext = settings.get('format')
        if ext is None:
            return Output(settings.copy(), file_name, file_path)

        ext = '.' + ext
        if ext in WriteHDF._ext:
            return WriteHDF(settings.copy(), file_name, file_path)

        if ext in WriteCSV._ext:
            return WriteCSV(settings.copy(), file_name, file_path)

        raise NotImplementedError("Invalid file format {}".format(ext))

    def save(
            self,
            data: Any,
            group: str,
            variation: Optional[Dict]=None,
            mode: Optional[str]='a',
            errored: Optional[bool]=False
        ) -> bool:
        """Save output

        Arguments:
           data: Data to be saved
           group: Description of simulation task
           variation: Parameter values
           mode: Save mode
           errored: Boolean describing success of simulation task

        Returns:
            `True` if data are saved successfully
        """
        raise NotImplementedError("Needs to be overloaded by derived methods")

    def dir(self) -> List[str]:
        """List previously saved cases"""
        raise NotImplementedError("Needs to be overloaded by derived methods")

    def load_like(self, group: str, other: Any) -> Any:
        """Load previously saved output

        Arguments:
           group: Label of entry to be loaded
           other: Object of the same type as the one to be loaded
        """
        raise NotImplementedError("Needs to be overloaded by derived methods")

    def save_metadata(
            self,
            metadata: Dict[str, Any]
        ) -> bool:
        """Save metadata

        Arguments:
            metadata: Metadata to be appended to the output file

        Returns:
            `True` if metadata are saved successfully
        """
        raise NotImplementedError("Needs to be overloaded by derived methods")


class WriteCSV(Output):
    """Class writing CSV output"""

    _ext = ['.csv']

    def save(self, data, group, variation=None, mode=None, errored=False):
        ""
        if not data:
            return
        if len(data) > 1:
            raise NotImplementedError("WriteCSV requires a simulation module returning single value")

        returns = self.kwargs.get('returns')

        key, value = next(iter(data.items()))

        if type(value).__name__ == 'Solution':

            if isinstance(ct, ImportError):
                raise ct # pylint: disable=raising-bad-type

            # use cantera native route to pandas.Series via SolutionArray.to_pandas
            arr = ct.SolutionArray(value, 1)
            value = arr.to_pandas(cols=list(returns.values())).iloc[0]

        elif type(value).__name__ == 'Mixture':

            # there is no native route in cantera
            out = []
            for k, v in returns.items():
                val = getattr(value, str(v))
                if hasattr(value, k) and isinstance(getattr(value, k), list):
                    out.extend(zip(getattr(value, k), val))
                else:
                    out.append((k, val))

            value = pd.Series(dict(out))

        if isinstance(value, pd.Series):

            if isinstance(variation, dict):
                var = {k.replace('.', '_'): v for k, v in variation.items()}
                value = pd.concat([pd.Series(var), value])

            row = pd.concat([pd.Series({'output': key}), value])

            fname = Path(self.output_name)
            if fname.is_file():
                df = pd.read_csv(fname)
            else:
                df = pd.DataFrame(columns=row.keys())
            df = df.append(row, ignore_index=True)
            df.to_csv(fname, index=False)

    def dir(self):
        ""
        fname = Path(self.output_name)
        if not fname.is_file():
            return []

        df = pd.read_csv(fname)
        return list(df.output)

    def load_like(self, group, other):
        ""
        raise NotImplementedError("Loader not implemented for '{}'".format(type(other).__name__))

    def save_metadata(self, metadata):
        ""
        # don't save metadata
        pass


class WriteHDF(Output):
    """Class writing HDF output"""

    _ext = ['.h5', '.hdf', '.hdf5']

    def save(self, data, group, variation=None, mode=None, errored=False):
        ""
        settings = self.settings
        if mode is None:
            mode = settings['mode']

        try:
            _save_hdf(data, settings, group, variation, mode, errored)
            return True
        except OSError as err:
            # Convert exception to warning
            msg = "Output of group '{}' failed with error message:\n{}".format(group, err)
            warnings.warn(msg, RuntimeWarning)
            return False

    def dir(self):
        ""
        fname = Path(self.output_name)
        if not fname.is_file():
            return []

        with h5py.File(fname, 'r') as hdf:
            keys = list(hdf.keys())
        return keys

    def load_like(self, group, other):
        ""
        if other is None:
            return None

        fname = Path(self.output_name)
        if not fname.is_file():
            return None

        with h5py.File(fname, 'r') as hdf:
            if group not in hdf.keys():
                return None

        if type(other).__name__ == 'SolutionArray':

            if isinstance(ct, ImportError):
                raise ct # pylint: disable=raising-bad-type

            extra = list(other._extra.keys())
            out = ct.SolutionArray(other.gas, extra=extra)
            out.read_hdf(fname, group=group)
            return out

        elif type(other).__name__ == 'FreeFlame':

            if isinstance(ct, ImportError):
                raise ct # pylint: disable=raising-bad-type

            out = ct.FreeFlame(other.gas)
            out.read_hdf(fname, group=group)
            return out

        raise NotImplementedError("Loader not implemented for '{}'".format(type(other).__name__))

    def save_metadata(self, metadata):
        ""
        if metadata is None:
            return None

        def _save_metadata(output_name, metadata):
            """Hidden module"""

            with h5py.File(output_name, 'r+') as hdf:
                for key, val in metadata.items():
                    if isinstance(val, dict):
                        hdf.attrs[key] = json.dumps(val)
                    else:
                        hdf.attrs[key] = val

        try:
            _save_metadata(self.output_name, metadata)
            return True
        except OSError as err:
            # Convert exception to warning
            msg = "Output of metadata failed with error message:\n{}".format(err)
            warnings.warn(msg, RuntimeWarning)
            return False


def _save_hdf(data, settings, group, variation, mode='a', errored=False):
    filename = settings.pop('name')
    settings.pop('mode')

    if filename is None:
        return

    filepath = settings.pop('path')
    force = settings.pop('force')
    settings.pop('format')

    if filepath is not None:
        filename = Path(filepath) / filename

    # file check
    fexists = Path(filename).is_file()

    if fexists:
        with h5py.File(filename, 'r') as hdf:
            for group in hdf.keys():
                if group in data and mode == 'a' and not force:
                    msg = 'Cannot overwrite existing ' \
                            'group `{}` (use force to override)'
                    raise RuntimeError(msg.format(group))
                elif group in data and mode == 'a' and force:
                    mode = 'w'

    settings.update(mode=mode)

    hdf_kwargs = {'mode', 'append', 'compression', 'compression_opts'}
    kwargs = {k: v for k, v in settings.items() if k in hdf_kwargs}

    if errored:
        with h5py.File(filename, mode) as hdf:
            for group, err in data.items():
                grp = hdf.create_group(group)
                grp.attrs[err[0]] = err[1]
    else:
        for group, states in data.items():
            # pylint: disable=no-member
            if type(states).__name__ == 'SolutionArray':
                if variation is not None:
                    attrs = variation
                else:
                    attrs = {}
                states.write_hdf(filename=filename, group=group,
                                 attrs=attrs, **kwargs)
            elif type(states).__name__ in ['FreeFlame']:
                if variation is not None:
                    description = '_'.join(['{}_{}'.format(k, v) for k, v in variation.items()])
                else:
                    description = None
                states.write_hdf(filename=filename, group=group,
                                 description=description, **kwargs)
