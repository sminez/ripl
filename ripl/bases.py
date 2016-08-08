import math as _math
import operator as op


class RiplSymbol(str):
    '''Internal representation of symbols'''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        return self.str

    def __hash__(self):
        return hash(self.str)

    def __eq__(self, other):
        try:
            return self.str == other.str
        except AttributeError:
            # comp to raw string
            return self.str == other


class RiplList(list):
    pass


class RiplNumeric:
    '''Base class for numerics'''
    pass


class RiplInt(RiplNumeric, int):
    def __new__(cls, num, *args, **kwargs):
        if isinstance(num, str):
            try:
                # Default to base 10
                _num = int(num, base=10)
            except ValueError:
                # Try to find the base
                base_prefixes = {"0b": 2, "0o": 8, "0x": 16}
                _num = None
                for prefix, base in base_prefixes.items():
                    if num.startswith(prefix):
                        _num = int(num, base=base)
                        break
                if not _num:
                    # We couldn't find a base that worked
                    raise ValueError
        return super(RiplInt, cls).__new__(cls, _num)


class RiplFloat(RiplNumeric, float):
    def __new__(cls, number, *args, **kwargs):
        number = float(number)
        return super(RiplFloat, cls).__new__(cls, number)


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
            RiplSymbol('+'): lambda *x: sum(x),  # For added LISPyness
            RiplSymbol('-'): op.sub,
            RiplSymbol('*'): op.mul,
            RiplSymbol('/'): op.truediv,
            RiplSymbol('>'): op.gt,
            RiplSymbol('<'): op.lt,
            RiplSymbol('>='): op.ge,
            RiplSymbol('<='): op.le,
            RiplSymbol('='): op.eq,
            RiplSymbol('append'): op.add,
            RiplSymbol('apply'): lambda x, xs: self[x](xs),
            RiplSymbol('begin'): lambda *x: x[-1],
            RiplSymbol('car'): lambda x: x[0],
            RiplSymbol('cdr'): lambda x: x[1:],
            RiplSymbol('cons'): lambda x, y: [x] + y,
            RiplSymbol('eq?'): op.is_,
            RiplSymbol('equal?'): op.eq,
            RiplSymbol('length'): len,
            RiplSymbol('list'): lambda *x: RiplList(x),
            RiplSymbol('list?'): lambda x: isinstance(x, RiplList),
            RiplSymbol('not'): op.not_,
            RiplSymbol('procedure?'): callable,
            RiplSymbol('null?'): lambda x: x == [],
            RiplSymbol('symbol?'): lambda x: isinstance(x, RiplSymbol),
            RiplSymbol('number?'): lambda x: isinstance(x, RiplNumeric),
        })
