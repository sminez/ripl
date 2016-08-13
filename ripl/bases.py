import functools
import operator as op


class Symbol:
    '''Internal representation of symbols'''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        # NOTE: not sure if this is a good idea...
        # raise NameError('name {} is not defined'.format(self.str))
        return self.str

    def __hash__(self):
        return hash(self.str)

    def __eq__(self, other):
        try:
            return self.str == other.str
        except AttributeError:
            # comp to raw string
            return self.str == other


class Env(dict):
    '''
    A dict of {Symbol('var'): val} pairs, with an outer Env.
    Used for storing and looking up the current environment.
    '''
    def __init__(self, args=[], arg_vals=[], outer=None,
                 use_standard=False, init_syntax=False):
        # Bind function arguments to the local scope
        self.update(zip([Symbol(p) for p in args], arg_vals))
        self.outer = outer
        if use_standard:
            self.init_standard_env()
        elif init_syntax:
            self.init_syntax()

    def find(self, var):
        '''Find the innermost Env where var appears.'''
        return self if (var in self) else self.outer.find(var)

    def init_standard_env(self):
        '''
        An environment with some standard procedures to get started.
        '''
        py_builtins = {Symbol(k): v for k, v in __builtins__.items()}
        self.update(py_builtins)

        std_ops = {
            Symbol('+'): lambda *x: functools.reduce(op.add, x),
            Symbol('-'): op.sub,
            Symbol('*'): op.mul,
            Symbol('/'): op.truediv,
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
            Symbol('cons'): lambda x, y: [x] + y,        # LISPy
            Symbol(':'): lambda x, y: [x] + y,           # Haskelly
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
        User defined macros will be stored in the same Env as these.(?)

        All macros will be passed a list of tokens, and executor that will
        handle eval and an environment to evaluate in.
        '''
        # NOTE: AttributeError will be caught and not passed up the call stack!
        def _quote(tokens, executor, env):
            '''
            Quote an atom or s-expression.
                (quote exp)
            '''
            # NOTE: This kind of works...but I haven't got unquoting
            #       working yet.
            return tokens[0]  # NOTE: this is always a list of a list!

        def _if(tokens, executor, env):
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
            exp = _true if executor.eval(test, env) else _false
            return executor.eval(exp, env) if exp else None

        def _define(tokens, executor, env):
            '''
            Bind a name to an expression
                (define name exp)
            '''
            name, expression = tokens
            env[name] = executor.eval(expression, env)

        def _eval(tokens, executor, env):
            '''
            Evaluate a bound symbol or quoted s-expression
                (eval sym) or (eval 'exp)
            '''
            tokens = tokens[0]
            if isinstance(tokens, list):
                # tokens are [quote, [ ... ]]
                val = executor.eval(tokens[1], env)
            else:
                # single token is a symbol, try to look it up
                try:
                    _val = env.find(Symbol(tokens))[tokens]
                except AttributeError:
                    raise NameError(
                        'undefined symbol {}'.format(tokens)
                        )
                val = executor.eval(_val, env)
            return val

        def _lambda(tokens, executor, env):
            '''
            Define a lambda funtion.
                (lambda (var ... ) (body))
            '''
            args, body = tokens
            return RiplFunc(args, body, env, executor)

        syntax = zip('quote if define eval lambda'.split(),
                     [_quote, _if, _define, _eval, _lambda])
        self.update({Symbol(k): v for k, v in syntax})


class RiplFunc:
    '''
    A user-defined function.
    NOTE: RiplFuncs are always declared using `lambda`.
    '''
    def __init__(self, args, body, env, executor):
        self.args = args
        self.body = body
        self.env = env
        self.executor = executor

    def __call__(self, *arg_vals):
        res = self.executor.eval(
                self.body,
                Env(
                    args=self.args,
                    arg_vals=arg_vals,
                    outer=self.env
                    )
                )
        return res
