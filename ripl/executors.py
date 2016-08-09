from pygments.token import Token

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .bases import Env
from .backend import Lexer, Parser
from .types import RiplSymbol, RiplList


class RiplExecutor:
    '''
    Base class for the Ripl interpretor and Ripl transpiler.
        Not sure whether to call it a compiler or not as it
        should eventually be able to output .py and .pyc
    '''
    def __init__(self):
        self.environment = Env(use_standard=True)
        self.lexer = Lexer()
        self.parser = Parser()

    def py_to_lisp_str(self, exp):
        '''
        Convert a Python object back into a Lisp-readable string for display.
        '''
        if isinstance(exp, RiplList):
            return '(' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        else:
            return str(exp)

    def eval_exp(self, x, env):
        '''
        Try to evaluate an expression in an environment.
        NOTE: Special language features and syntax found here.
        '''
        # TODO: Break this into smaller, more testable chunks
        if not isinstance(x, list):  # constant literal
            try:
                # Check to see if we have this in the current environment.
                return env.find(RiplSymbol(x))[x]
            except AttributeError:
                # We bottomed out so return it raw
                return x
        elif x[0] == 'quote':          # (quote exp)
            # NOTE: This kind of works...but I haven't got unquoting
            #       working yet.
            # TODO: Convert back to RIPL/LISP representation?
            _, exp = x
            return exp
        elif x[0] == 'if':             # (if test conseq alt)
            _, test, conseq, alt = x
            exp = conseq if self.eval_exp(test, env) else alt
            return self.eval_exp(exp, env)
        elif x[0] == 'define':         # (define var exp)
            _, var, exp = x
            env[var] = self.eval_exp(exp, env)
        elif x[0] == 'set!':           # (set! var exp)
            _, var, exp = x
            env.find(var)[var] = self.eval_exp(exp, env)
        elif x[0] == 'lambda':         # (lambda (var...) body)
            _, parms, body = x
            return Procedure(parms, body, env)
        else:                          # (proc arg...)
            proc = self.eval_exp(x[0], env)
            args = [self.eval_exp(exp, env) for exp in x[1:]]
            return proc(*args)

    def make_procedure(self, parms, body, env):
        def _call_proc(self, *args):
            return self.eval_exp(body, Env(parms, args, env))

        proc = Procedure(parms, body, env)
        proc.__call__ = _call_proc


class RiplRepl(RiplExecutor):
    def __init__(self):
        self.completer = WordCompleter(
            ('apply begin car cdr cons defn '
             'eq? equal? list? symbol? number? '
             'null? append length').split(),
            ignore_case=False)
        super().__init__()

    def get_continuation_tokens(self, cli, width):
        '''For use with multiline input when I get that working...'''
        return [(Token, '~' * width)]

    def eval_and_print(self, exp, env):
        '''
        Attempt to evaluate an expresion in an execution environment.
        Catches and displays output and exceptions.
        '''
        try:
            val = self.eval_exp(exp, env)
            if val is not None:
                print('> ' + self.py_to_lisp_str(val) + '\n')
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))

    def repl(self, prompt_str='ζ > '):
        '''
        The main read eval print loop for RIPL.
        Uses prompt_toolkit:
            http://python-prompt-toolkit.readthedocs.io/en/stable/
        '''
        def exit_message():
            print('\nThanks for giving RIPL a try!\nさようなら!\n')

        if not self.environment:
            raise EnvironmentError('Could not find execution environment')

        print('<{[( RIPL Is Pythonic LISP )]}>\n'
              'Start typing a lisp expressions!\n'
              '(Type `quit` to quit)')

        history = InMemoryHistory()

        try:
            while True:
                user_input = prompt(
                        prompt_str,
                        history=history,
                        multiline=False,
                        wrap_lines=True,
                        mouse_support=True,
                        completer=self.completer,
                        auto_suggest=AutoSuggestFromHistory())

                if user_input:
                    if user_input == 'quit':
                        exit_message()
                        break
                    else:
                        # Attempt to parse an expression and
                        # display any exceptions to the user.
                        raw_tokens = self.lexer.get_tokens(user_input)
                        parsed_tokens = self.parser.parse(raw_tokens)
                        self.eval_and_print(parsed_tokens, self.environment)
        except (EOFError, KeyboardInterrupt):
            # User hit Ctl+d
            exit_message()


class Procedure:
    '''
    A user-defined LISP procedure.
    '''
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
