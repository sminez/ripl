'''
Utility functions and helpers for use in RIPL
    NOTE: These are not intended to be used directly by the user!

Tail calls...
http://www.kylem.net/programming/tailcall.html
http://stackoverflow.com/questions/13591970/does-python-optimize-tail-recursion
'''
from .types import RiplSymbol
from .types import RiplNumeric, RiplString

from functools import partial
from importlib import import_module


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


def pyimport(module, env, _as=None, _from=None):
    '''
    Import a module and insert it into the given environment.
    --> This will perform inports with local scope.

    Args:
        _as   :: str <Name to bind the module under>
        _form :: list[str] <List of submodules to import>
    '''
    # TODO: Find out if python imports are always global.
    if _as and _from:
        # Can't do `from foo as bar import baz`
        raise SyntaxError('Invalid import')

    # Grab the module from sys.modules
    raw = import_module(module)
    mod = vars(raw).items()

    if _as:
        defs = {RiplSymbol('{}.{}'.format(_as, k)): v for k, v in mod}
        env.update(defs)
    elif _from:
        defs = {RiplSymbol(k): v for k, v in mod if k in _from}
        env.update(defs)
    else:
        defs = {RiplSymbol('{}.{}'.format(module, k)): v for k, v in mod}
        env.update(defs)

    return env


def curry(func, *args, **kwargs):
    '''
    Just an alias to functools.partial
        functools will use the _functools c version where possible

    add3 = curry(op.add, 3)
    add3(1) == 4

    RIPL SYNTAX
        Going to try having a curry macro that is invoked as:
        (define add3 ~(add 3))

    This needs to be handled at the parsing stage...
    '''
    return partial(func, *args, **kwargs)
