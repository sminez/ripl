import math as _math
import operator as op

from .utils import ripl_add
from .types import RiplSymbol, RiplString
from .types import RiplNumeric, RiplInt, RiplFloat
from .types import RiplTuple, RiplDict, RiplList


class Env(dict):
    '''
    A dict of {RiplSymbol('var'): val} pairs, with an outer Env.
    Used for storing and looking up the current environment.
    '''
    def __init__(self, parms=(), args=(), outer=None, use_standard=False):
        self.update(zip([RiplSymbol(p) for p in parms], args))
        self.outer = outer
        if use_standard:
            self.init_standard_env()

    def find(self, var):
        '''Find the innermost Env where var appears.'''
        return self if (var in self) else self.outer.find(var)

    def init_standard_env(self):
        '''
        An environment with some Scheme standard procedures to get started.
        '''
        math_syms = {RiplSymbol(k): v for k, v in vars(_math).items()}
        builtins = {RiplSymbol(k): v for k, v in __builtins__.items()}
        self.update(math_syms)
        self.update(builtins)
        self.update({
            RiplSymbol('+'): ripl_add,  # Using a custom add for LISPyness
            RiplSymbol('-'): op.sub,
            RiplSymbol('*'): op.mul,
            RiplSymbol('/'): op.truediv,
            RiplSymbol('>'): op.gt,
            RiplSymbol('<'): op.lt,
            RiplSymbol('>='): op.ge,
            RiplSymbol('<='): op.le,
            RiplSymbol('=='): op.eq,
            RiplSymbol('!='): op.ne,
            RiplSymbol('append'): op.add,
            RiplSymbol('apply'): lambda x, xs: self[x](xs),  # need find?
            RiplSymbol('begin'): lambda *x: x[-1],
            RiplSymbol('car'): lambda x: x[0],
            RiplSymbol('cdr'): lambda x: x[1:],
            RiplSymbol('cons'): lambda x, y: [x] + y,
            RiplSymbol(':'): lambda x, y: [x] + y,  # Haskelly
            RiplSymbol('length'): len,
            RiplSymbol('str'): lambda x: RiplString(x),
            RiplSymbol('string'): lambda x: RiplString(x),
            RiplSymbol('sym'): lambda x: RiplSymbol(x),
            RiplSymbol('int'): lambda x: RiplInt(x),
            RiplSymbol('float'): lambda x: RiplFloat(x),
            RiplSymbol('dict'): lambda *x: RiplDict(x),
            RiplSymbol('list'): lambda *x: RiplList(x),
            RiplSymbol('tuple'): lambda *x: RiplTuple(x),
            RiplSymbol(','): lambda *x: RiplTuple(x),
            RiplSymbol('not'): op.not_,
            RiplSymbol('eq?'): op.is_,
            RiplSymbol('equal?'): op.eq,
            RiplSymbol('procedure?'): callable,
            RiplSymbol('null?'): lambda x: x == [],
            RiplSymbol('string?'): lambda x: isinstance(x, RiplString),
            RiplSymbol('symbol?'): lambda x: isinstance(x, RiplSymbol),
            RiplSymbol('int?'): lambda x: isinstance(x, RiplInt),
            RiplSymbol('float?'): lambda x: isinstance(x, RiplFloat),
            RiplSymbol('number?'): lambda x: isinstance(x, RiplNumeric),
            RiplSymbol('dict?'): lambda x: isinstance(x, RiplDict),
            RiplSymbol('tuple?'): lambda x: isinstance(x, RiplTuple),
            RiplSymbol('list?'): lambda x: isinstance(x, RiplList),
        })
