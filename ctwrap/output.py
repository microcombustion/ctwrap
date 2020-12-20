"""The :py:mod:`output` module defines helper functions used for file output
"""

from pathlib import Path
import h5py
import json

from typing import Dict, Any, Optional, Union


supported = ('.h5', '.hdf', '.hdf5')


def _parse_output(out: Dict[str, Any],
                  fname: Optional[str] = None,
                  fpath: Optional[str] = None):
    """
    Parse output dictionary (hidden function)
    Overrides defaults with keyword arguments.

    Arguments:
        out: dictionary from yaml input
        fname: filename (overrides yaml)
        fpath: output path (overrides yaml)

    Returns:
        Dictionary containing output information
    """

    if out is None:
        return None

    # establish defaults
    out = out.copy()
    out['path'] = None  # should never be specified inside of yaml
    if 'format' not in out:
        out['format'] = ''
    if 'force_overwrite' not in out:
        out['force_overwrite'] = False

    fformat = out['format']

    # file name keyword overrides dictionary
    if fname is not None:

        # fname may contain path information
        head = Path(fname).parent
        fname = Path(fname).name
        if str(head) != "." and fpath is not None:
            raise RuntimeError('contradictory specification')
        elif str(head) != ".":
            fpath = head

        fname = Path(fname).stem
        ext = Path(fname).suffix
        if ext in supported:
            fformat = ext

        out['name'] = fname

    # file path keyword overrides dictionary
    if fpath is not None:
        out['path'] = fpath

    # file format
    if fformat is None:
        pass
    elif len(fformat):
        out['format'] = fformat.lstrip('.')
    else:
        out['format'] = 'h5'

    if fformat is None:
        out['file_name'] = None
    else:
        out['file_name'] = '.'.join([out['name'], out['format']])

    return out

def _save_hdf(data, output, task, mode='a', errored=False):

    filename = output.pop('file_name')

    if filename is None:
        return

    filepath = output.pop('path')
    force = output.pop('force_overwrite')

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

    output.pop('name')
    output.update(mode=mode)

    if errored:
        with h5py.File(filename, mode) as hdf:
            for group, err in data.items():
                grp = hdf.create_group(group)
                grp.attrs[err[0]] = err[1]
    else:
        for group, states in data.items():
            # pylint: disable=no-member
            if type(states).__name__ == 'SolutionArray':
                attrs = {'description': task}
                states.write_hdf(filename=filename, group=group,
                                    attrs=attrs, **output)
            elif type(states).__name__ in ['FreeFlame']:
                states.write_hdf(filename=filename, group=group,
                                    description=task, **output)

def _save_metadata(output: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   ) -> None:
    """
    Modules saves the input file as an attribute after the
    batch simulation has been completed

    This method calls the
    :py:func:`~ctwrap.parser.save_metadata` method.

    Arguments:
        metadata (dict): data to be saved
        output (dict): output file information
    """

    if metadata is None or output is None:
        return

    oname = output['file_name']
    opath = output['path']
    #formatt = output['format']
    #force = output['force_overwrite']

    if oname is None:
        return
    if opath is not None:
        oname = Path(opath) / oname

    with h5py.File(oname, 'r+') as hdf:
        for key, val in metadata.items():
            if isinstance(val, dict):
                hdf.attrs[key] = json.dumps(val)
            else:
                hdf.attrs[key] = val
