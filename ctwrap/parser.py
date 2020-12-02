"""Parser object."""
from typing import Dict, Any, Union, Tuple, List

from pint import UnitRegistry

ureg = UnitRegistry()

__all__ = ['Parser']


class Parser(object):
    """
    A lightweight class that handles units.

    The handling mimics that of a python dictionary, while adding direct access to
    keyed values via attributes.
    """

    def __init__(self, dct: Dict[str, Any]) -> None:
        """
        Constructor

        Argument:
            dct (dict) : dictionary to be parsed
        """

        self.raw = dct

    def __getattr__(self, attr: str) -> str:
        """
        Get attribute

        Arguments:
             attr (str): attribute

        Returns:
            Atrribute
        """

        if attr not in self.raw:
            raise AttributeError("unknown attribute '{}'".format(attr))

        return self[attr]

    def __getitem__(self, key: str) -> Union[str, bool, float, Tuple]:
        """
        Get item

        Argument:
            key (str): key

        Returns:
            Corresponding values from the key

        """

        val = self.raw[key]

        if isinstance(val, (str, bool, int, float)):
            return val
        elif isinstance(val, list) and len(val) > 0:
            return ureg.Quantity(val[0], ureg[val[1]])

    def __repr__(self):
        return repr(self.raw)

    def keys(self) -> List:
        """
        Returns list of keys
        """
        return self.raw.keys()
