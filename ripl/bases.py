import functools
import collections
import collections.abc
import operator as op


class Symbol:
    '''
    Internal representation of symbols
    Symbols can be bound to values using (define Symbol Value)
    '''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        return self.str

    def __hash__(self):
        return hash(self.str)

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.str == other.str


class Keyword:
    '''
    Internal representation of Keywords
    Unlike symbols, keywords can only refer to themselves
        i.e. (define :keyword "foo") is a syntax error
    Main intended use is for keys in dicts.
    '''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        return ':' + self.str

    def __hash__(self):
        return hash(':' + self.str)

    def __eq__(self, other):
        if isinstance(other, Keyword):
            return self.str == other.str
        else:
            return False

    def _keyword_comp(self, other):
        '''Used for when we store something as a keyword internally'''
        if isinstance(other, Keyword):
            return self == other
        elif isinstance(other, Symbol):
            return self.str == other.str
        else:
            return self.str == other


class RList(collections.abc.MutableSequence):
    '''Attempt at a LISP style linked list'''
    def __init__(self, data=None):
        if data:
            self.data = collections.deque(data)
        else:
            self.data = collections.deque()

    def __eq__(self, other):
        if not isinstance(other, RList):
            return False
        else:
            return self.data == other.data

    def __iter__(self):
        return iter(self.data)

    def _cons(self, other):
        # Need to reverse otherwise (cons '(1 2) `(3 4)) -> (2 1 3 4)
        try:
            self.data.extendleft(iter(other))
            return self
        except:
            self.data.extendleft([other])
            return self

    def __call__(self, index):
        '''Collections are mappings to values'''
        return self[index]

    def __repr__(self):
        return '(' + ' '.join([str(x) for x in self.data]) + ')'

    def __getitem__(self, key):
        '''Hack slicing onto deques'''
        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            start = start if start else 0
            stop = stop if stop else len(self)
            step = step if step else 1
            return RList([self.data[x] for x in range(start, stop, step)])
        else:
            return self.data[key]

    def __delitem__(self, index):
        del self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def insert(self, index, value):
        self.data.insert(index, value)

    def __len__(self):
        return len(self.data)

    def __add__(self, other):
        new = RList(self.data + other.data)
        return new


class EmptyList(RList):
    def __eq__(self, other):
        if other is None:
            return True
        else:
            if isinstance(other, RList):
                if len(other) == 0:
                    return True
                else:
                    return other is None

    def __add__(self, other):
        # Don't want to pass on the `self == None` behaviour
        return RList(other)


class RVector(list):
    '''Python lists are really vectors so rename them and make cons work'''
    def _cons(self, other):
        '''cons should always extend on the left'''
        return RVector([other]) + self

    def __call__(self, index):
        '''Collections are mappings to values'''
        return self[index]


class RDict(dict):
    '''Make cons work for dicts'''
    def _cons(self, other):
        '''as dicts have no order, just update if possible'''
        if isinstance(other, dict):
            self.update(other)
        else:
            pairs = [other[i:i+2] for i in range(0, len(other), 2)]
            self.update({k: v for k, v in pairs})
        return self


class RString(str):
    '''Make cons work and make sure str != Keyword/Symbol'''
    def __init__(self, string):
        self.str = string

    def _cons(self, other):
        return other + self

    def __eq__(self, other):
        if isinstance(other, Symbol) or isinstance(other, Keyword):
            return False
        else:
            try:
                # comp to RString
                return self.str == other.str
            except:
                # comp to raw string
                return self.str == other

    def __hash__(self):
        return hash(self.str)


# See: https://docs.python.org/3.5/library/collections.html
# RIPL functions are closures, implemented as a reference to the
# current Scope when they are defined.
#     NOTE: Scopes - like all other things in RIPL - are first class
#           values that can be passed and manipulated.
#       --> Alterations to an outer Scope do not leave the execution
#           of the function making the change.
Scope = collections.ChainMap


def nested_scope(current_scope, args=[], vals=[]):
    '''
    Wrapper for the ChainMap.new_child() method that allows
    for *args and **kwargs like behaviour:

    Note: this is not currently using the **{dict} syntax
          to splat the dict... :(

    nested_scope(scope, 'a', 1)
    >> ChainMap({'a': 1}, {<scope>})
    nested_scope(scope, '*args', [1, 2, 3])
    >> ChainMap({'args': [1, 2, 3]}, {<scope>})
    nested_scope(scope, '**kwargs', {'a': 1, 'b': 2})
    >> ChainMap({'a': 1, 'b': 2}, {<scope>})
    nested_scope(scope, ('a', 'b'), [1, 2])
    >> ChainMap({'a': 1, 'b': 2}, {<scope>})
    '''
    # TODO: Find a way of lexing kwargs to return a dict
    #       i.e. (foo (a=1 b=2)) -> (foo {a: 1, b: 2})
    if len(args) == 1:
        arg = args[0]
        # Check to see if we have *args or **kwargs
        if arg.str.startswith('**'):
            # try to extract kwargs and splat them in
            if isinstance(vals, dict):
                new_defs = vals
            else:
                # This isn't exactly the same as Pythons **kwargs
                # TODO: match python style
                raise SyntaxError('**kwargs must be a dict')
        elif arg.str.startswith('*'):
            # try to splat in the values provided
            if len(vals) > 1:
                vals = tuple(vals)
            else:
                vals = vals[0]
            new_defs = {Symbol(arg.str.lstrip('*')): vals}
        else:
            # This should be a single arg and val
            if len(vals) != 1:
                raise SyntaxError(
                    'expected 1 positional argument, got {}'.format(len(vals)))
            new_defs = {arg: vals[0]}
    else:
        if len(args) > len(vals):
            raise SyntaxError('missing positional arguments')
        if len(args) < len(vals):
            raise SyntaxError('too many positional arguments')
        else:
            new_defs = {var: val for var, val in zip(args, vals)}

    return current_scope.new_child(new_defs)


def get_global_scope():
    '''
    Build a scope with some standard procedures to get started.
    '''
    py_builtins = {Symbol(k): v for k, v in __builtins__.items()}

    std_ops = {
        Symbol('+'): lambda *x: functools.reduce(op.add, x),
        Symbol('-'): op.sub,
        Symbol('*'): op.mul,
        Symbol('/'): op.truediv,
        Symbol('%'): op.mod,
        Symbol('>'): op.gt,
        Symbol('<'): op.lt,
        Symbol('>='): op.ge,
        Symbol('<='): op.le,
        Symbol('=='): op.eq,
        Symbol('!='): op.ne
        }

    key_words = {
        Symbol('append'): op.add,
        Symbol('apply'): lambda x, xs: scope[x](xs),  # need find?
        Symbol('begin'): lambda *x: x[-1],
        Symbol('car'): lambda x: x[0],
        Symbol('cdr'): lambda x: x[1:],
        Symbol('cons'): lambda x, y: y._cons(x),     # LISPy
        Symbol(':'): lambda x, y: y._cons(x),        # Haskelly
        Symbol('and'): op.and_,
        Symbol('or'): op.or_,
        Symbol('not'): op.not_,
        Symbol('len'): len,
        }

    type_cons = {
        Symbol('str'): lambda x: RString(x),
        Symbol('int'): lambda x: int(x),
        Symbol('float'): lambda x: float(x),
        Symbol('complex'): lambda x: complex(x),
        Symbol('dict'): lambda *x: RDict(x),
        Symbol('list'): lambda *x: RList(x),
        Symbol('vector'): lambda *x: list(x),
        Symbol('tuple'): lambda *x: tuple(x),
        Symbol(','): lambda *x: tuple(x)
        }

    bool_tests = {
        Symbol('eq?'): op.is_,
        Symbol('equal?'): op.eq,
        Symbol('callable?'): callable,
        Symbol('null?'): lambda x: x == EmptyList(),
        Symbol('string?'): lambda x: isinstance(x, str),
        Symbol('symbol?'): lambda x: isinstance(x, Symbol),
        Symbol('dict?'): lambda x: isinstance(x, dict),
        Symbol('tuple?'): lambda x: isinstance(x, tuple),
        Symbol('list?'): lambda x: isinstance(x, list),
        Symbol('int?'): lambda x: isinstance(x, int),
        Symbol('float?'): lambda x: isinstance(x, float),
        Symbol('number?'): lambda x: type(x) in [int, float, complex],
    }

    scope = Scope(py_builtins)
    for defs in [std_ops, key_words, type_cons, bool_tests]:
        scope.update(defs)
    return scope


class Func:
    '''
    A user-defined function.
    '''
    def __init__(self, args, docstring, body, scope, evaluator):
        self.args = args
        self.body = body
        self.scope = scope
        self.evaluator = evaluator
        self.__doc__ = docstring

    def __call__(self, *arg_vals):
        res = self.evaluator.eval(
                self.body,
                nested_scope(
                    current_scope=self.scope,
                    args=self.args,
                    vals=arg_vals))
        return res
