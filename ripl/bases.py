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
        try:
            self.extendleft(iter(other))
            return self
        except:
            self.extendleft([other])
            return self


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
        Symbol('not'): op.not_,
        Symbol('len'): len
        }

    type_cons = {
        Symbol('str'): lambda x: RString(x),
        Symbol('int'): lambda x: int(x),
        Symbol('float'): lambda x: float(x),
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


def get_syntax():
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
            (if (test) (then) (else)) or (if (test) (then))
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
        Bind a name to a value or the value of an expression
            (define var (exp)) or (define var val)
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
                _val = scope[tokens]
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
        try:
            assert(len(tokens) == 2)
            assert(isinstance(tokens[0], RList))
            assert(isinstance(tokens[1], RList))
        except AssertionError:
            raise SyntaxError('lambda takes two lists as arguments')

        args, body = tokens
        return RiplFunc(args, 'anonymous lambda', body, scope, evaluator)

    def _defn(tokens, evaluator, scope):
        '''
        Sugar for defining a function:
            (defn foo <"""docstr"""> (bar baz) (== bar baz))
                      ~~~~~~~~~~~~~~ <- optional
        '''
        try:
            if len(tokens) == 4:
                docstring = tokens.pop(1)
            else:
                docstring = None
            assert(len(tokens) == 3)
            assert(isinstance(tokens[0], Symbol))
            assert(isinstance(tokens[1], RList))
            assert(isinstance(tokens[2], RList))
        except AssertionError:
            raise SyntaxError('defn takes a symbol and two lists as arguments')

        name, args, body = tokens
        scope[name] = RiplFunc(args, docstring, body, scope, evaluator)

    def _let(tokens, evaluator, scope):
        '''
        Let has two forms:
            (let ((var1 val1) (var2 val2) ...) (body))
            (let name ((var1 val1) (var2 val2) ...) (body))
        In the second form, `name` is bound to `body` and can be called from
        inside itself.
        In both versions, `var1`..`varn` are bound in a new local scope for the
        execution of `body`.
        '''
        if len(tokens) == 2:
            _vars, _body = tokens
            _name = 'anonymous lambda'
            bind_self = False
        else:
            _name, _vars, _body = tokens
            bind_self = True
        args = [v[0] for v in _vars]
        vals = [v[1] for v in _vars]
        let = RiplFunc(args, _name, _body, scope, evaluator)
        if bind_self:
            let.scope = let.scope.new_child({_name: let})
        return let(vals)

    syntax = zip('quote if define defn eval lambda let'.split(),
                 [_quote, _if, _define, _defn, _eval, _lambda, _let])

    syntax_scope = Scope({Symbol(k): v for k, v in syntax})

    return syntax_scope


class RiplFunc:
    '''
    A user-defined function.
    NOTE: RiplFuncs are always declared using `lambda`.
          The def{x} syntax is desugared in the lexer.
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
