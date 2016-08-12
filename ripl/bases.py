import operator as op

from .utils import _ripl_add
from .types import RiplSymbol, RiplString
from .types import RiplNumeric, RiplInt, RiplFloat
from .types import RiplTuple, RiplDict, RiplList


class Env(dict):
    '''
    A dict of {RiplSymbol('var'): val} pairs, with an outer Env.
    Used for storing and looking up the current environment.
    '''
    def __init__(self, args=[], arg_vals=[], outer=None,
                 use_standard=False, init_syntax=False):
        # Bind function arguments to the local scope
        self.update(zip([RiplSymbol(p) for p in args], arg_vals))
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
        py_builtins = {RiplSymbol(k): v for k, v in __builtins__.items()}
        self.update(py_builtins)

        std_ops = {
            RiplSymbol('+'): _ripl_add,  # Using a custom add for LISPyness
            RiplSymbol('-'): op.sub,
            RiplSymbol('*'): op.mul,
            RiplSymbol('/'): op.truediv,
            RiplSymbol('>'): op.gt,
            RiplSymbol('<'): op.lt,
            RiplSymbol('>='): op.ge,
            RiplSymbol('<='): op.le,
            RiplSymbol('=='): op.eq,
            RiplSymbol('!='): op.ne
            }

        key_words = {
            RiplSymbol('append'): op.add,
            RiplSymbol('apply'): lambda x, xs: self[x](xs),  # need find?
            RiplSymbol('begin'): lambda *x: x[-1],
            RiplSymbol('car'): lambda x: x[0],
            RiplSymbol('cdr'): lambda x: x[1:],
            RiplSymbol('cons'): lambda x, y: [x] + y,        # LISPy
            RiplSymbol(':'): lambda x, y: [x] + y,           # Haskelly
            RiplSymbol('not'): op.not_,
            RiplSymbol('length'): len
            }

        type_cons = {
            RiplSymbol('str'): lambda x: RiplString(x),
            RiplSymbol('sym'): lambda x: RiplSymbol(x),
            RiplSymbol('int'): lambda x: RiplInt(x),
            RiplSymbol('float'): lambda x: RiplFloat(x),
            RiplSymbol('dict'): lambda *x: RiplDict(x),
            RiplSymbol('list'): lambda *x: RiplList(x),
            RiplSymbol('tuple'): lambda *x: RiplTuple(x),
            RiplSymbol(','): lambda *x: RiplTuple(x)
            }

        bool_tests = {
            RiplSymbol('eq?'): op.is_,
            RiplSymbol('equal?'): op.eq,
            RiplSymbol('callable?'): callable,
            RiplSymbol('null?'): lambda x: x == [],
            RiplSymbol('string?'): lambda x: isinstance(x, RiplString),
            RiplSymbol('symbol?'): lambda x: isinstance(x, RiplSymbol),
            RiplSymbol('int?'): lambda x: isinstance(x, RiplInt),
            RiplSymbol('float?'): lambda x: isinstance(x, RiplFloat),
            RiplSymbol('number?'): lambda x: isinstance(x, RiplNumeric),
            RiplSymbol('dict?'): lambda x: isinstance(x, RiplDict),
            RiplSymbol('tuple?'): lambda x: isinstance(x, RiplTuple),
            RiplSymbol('list?'): lambda x: isinstance(x, RiplList)
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
            tokens = tokens[0]  # NOTE: this is always a list of a list!
            if type(tokens) == list:
                return RiplList(tokens)
            else:
                return tokens

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
                    _val = env.find(RiplSymbol(tokens))[tokens]
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
        self.update({RiplSymbol(k): v for k, v in syntax})


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
