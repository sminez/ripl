'''
Common LISPy / Haskelly functions to use inside RIPL
'''
from .types import RiplNumeric


def ripl_add(*args):
    numeric = all([isinstance(x, RiplNumeric) for x in args])
    if numeric:
        return sum(args)
    else:
        # We should have strings so join them
        return ''.join(args)


def reverse(arg):
    return arg[::-1]
