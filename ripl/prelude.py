'''
Common LISPy / Haskelly functions to use inside RIPL
'''
from .types import RiplNumeric, RiplString


def ripl_add(*args):
    '''
    Add an arbitrary number of numerics or cat
    an arbitrary number of strings together.
    '''
    numeric = all([isinstance(x, RiplNumeric) for x in args])
    if numeric:
        return sum(args)
    else:
        if not all([isinstance(x, RiplString) for x in args]):
            raise TypeError("Can't add strings and numerics")
        # We should have strings so join them
        return ''.join(args)


def reverse(arg):
    '''Reverse an iterable'''
    return arg[::-1]
