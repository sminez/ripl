import functools
import collections
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


class RList(collections.deque):
    '''Attempt at a LISP style linked list'''
    def _cons(self, other):
        # Need to reverse otherwise (cons '(1 2) `(3 4)) -> (2 1 3 4)
        for elem in other[::-1]:
            self.extendleft(elem)


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
        return other + self

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


class Scope(collections.ChainMap):
    '''
    See: https://docs.python.org/3.5/library/collections.html

    A dict of {Symbol('var'): val} pairs, with a single outer Scope
    enclosing it unless it is the GLOBAL Scope.
        These are used to store and looking up the current scope of an
        operation.

    RIPL functions are closures, implemented as a reference to the
    current Scope when they are defined.
        NOTE: Scopes - like all other things in RIPL - are first class
              values that can be passed and manipulated.
          --> Alterations to an outer Scope do not leave the execution
              of the function making the change.
    '''
    def __init__(self, args=[], arg_vals=[],
                 use_standard=False, init_syntax=False):
        super().__init__()
        # Bind function arguments to the local scope
        self.update(zip([Symbol(p) for p in args], arg_vals))
        if use_standard:
            self.init_standard_scope()
            self.CONTAINS_SYNTAX = False
        elif init_syntax:
            self.init_syntax()
            # Using as a flag to avoid importing regular modules
            self.CONTAINS_SYNTAX = True

    def _inner_scope(self, args=[], arg_vals=[]):
        '''
        Build a new scope that is the child of this one.
        Optionally bind in new paramaters
        '''
        inner_scope = self.new_child()
        if len(args) == 1:
            if isinstance(arg_vals, dict):
                # Should be equivalent to **kwargs
                inner_scope.update(arg_vals)
            else:
                # This should be the equivalent of *args
                inner_scope.update({Symbol(args): [a for a in arg_vals]})
        else:
            inner_scope.update(zip([Symbol(p) for p in args], arg_vals))

        return inner_scope

    def init_standard_scope(self):
        '''
        A scope with some standard procedures to get started.
        '''
        py_builtins = {Symbol(k): v for k, v in __builtins__.items()}
        self.update(py_builtins)

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
            Symbol('apply'): lambda x, xs: self[x](xs),  # need find?
            Symbol('begin'): lambda *x: x[-1],
            Symbol('car'): lambda x: x[0],
            Symbol('cdr'): lambda x: x[1:],
            Symbol('cons'): lambda x, y: y._cons(x),     # LISPy
            Symbol(':'): lambda x, y: y._cons(x),        # Haskelly
            Symbol('not'): op.not_,
            Symbol('length'): len
            }

        type_cons = {
            Symbol('str'): lambda x: str(x),
            Symbol('int'): lambda x: int(x),
            Symbol('float'): lambda x: float(x),
            Symbol('dict'): lambda *x: dict(x),
            Symbol('list'): lambda *x: list(x),
            Symbol('tuple'): lambda *x: tuple(x),
            Symbol(','): lambda *x: tuple(x)
            }

        bool_tests = {
            Symbol('eq?'): op.is_,
            Symbol('equal?'): op.eq,
            Symbol('callable?'): callable,
            Symbol('null?'): lambda x: x == [],
            Symbol('string?'): lambda x: isinstance(x, str),
            Symbol('symbol?'): lambda x: isinstance(x, Symbol),
            Symbol('dict?'): lambda x: isinstance(x, dict),
            Symbol('tuple?'): lambda x: isinstance(x, tuple),
            Symbol('list?'): lambda x: isinstance(x, list),
            Symbol('int?'): lambda x: isinstance(x, int),
            Symbol('float?'): lambda x: isinstance(x, float),
            Symbol('number?'): lambda x: type(x) in [int, float, complex],
        }

        for defs in [std_ops, key_words, type_cons, bool_tests]:
            self.update(defs)

    def init_syntax(self):
        '''
        Built-in language features for use in the evaluator.
        User defined macros will be stored in the same Scope as these.(?)

        All macros will be passed a list of tokens, and evaluator that will
        handle eval and an scope to evaluate in.
        '''
        # NOTE: AttributeError will be caught and not passed up the call stack!
        def _quote(tokens, evaluator, scope):
            '''
            Quote an atom or s-expression.
                (quote exp) or '(exp)
            '''
            # NOTE: Only atoms and s-expressions can be quoted. Other
            #       collections act as quoted atoms by default as calling
            #       them is a Collection -> value call.
            return tokens[0]

        def _if(tokens, evaluator, scope):
            '''
            Evaluate an if statement.
                (if test then else) or (if test then)
            '''
            if len(tokens) == 3:
                test, _true, _false = tokens
            elif len(tokens) == 2:
                test, _true = tokens
                _false = None
            else:
                msg = 'if expression requires 2 or 3 clauses: got {}'
                raise SyntaxError(msg.format(len(tokens)))
            exp = _true if evaluator.eval(test, scope) else _false
            return evaluator.eval(exp, scope) if exp else None

        def _define(tokens, evaluator, scope):
            '''
            Bind a name to an expression
                (define name exp)
            '''
            name, expression = tokens
            scope[name] = evaluator.eval(expression, scope)

        def _eval(tokens, evaluator, scope):
            '''
            Evaluate a bound symbol or quoted s-expression
                (eval sym) or (eval 'exp)
            '''
            tokens = tokens[0]
            if isinstance(tokens, list):
                # tokens are [quote, [ ... ]]
                val = evaluator.eval(tokens[1], scope)
            else:
                # single token is a symbol, try to look it up
                try:
                    _val = scope.find(Symbol(tokens))[tokens]
                except AttributeError:
                    raise NameError(
                        'undefined symbol {}'.format(tokens)
                        )
                val = evaluator.eval(_val, scope)
            return val

        def _lambda(tokens, evaluator, scope):
            '''
            Define a lambda funtion.
                (lambda (var ... ) (body))
            '''
            args, body = tokens
            return RiplFunc(args, body, scope, evaluator)

        syntax = zip('quote if define eval lambda'.split(),
                     [_quote, _if, _define, _eval, _lambda])
        self.update({Symbol(k): v for k, v in syntax})


class RiplFunc:
    '''
    A user-defined function.
    NOTE: RiplFuncs are always declared using `lambda`.
          The def{x} syntax is desugared in the lexer.
    '''
    def __init__(self, args, body, scope, evaluator):
        self.args = args
        self.body = body
        self.scope = scope
        self.evaluator = evaluator

    def __call__(self, *arg_vals):
        res = self.evaluator.eval(
                self.body,
                self.scope._inner_scope(args=self.args, arg_vals=arg_vals))
        return res
