from pygments.token import Token

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

from .bases import Env
from .backend import Lexer, Parser
from .types import RiplSymbol, RiplList

import ripl.prelude as prelude


class RiplExecutor:
    '''
    Base class for the Ripl interpretor and Ripl transpiler.
        Not sure whether to call it a compiler or not as it
        should eventually be able to output .py and .pyc
    '''
    def __init__(self, use_prelude=True):
        self.environment = Env(use_standard=True)
        if use_prelude:
            funcs = {RiplSymbol(k): v for k, v in vars(prelude).items()}
            self.environment.update(funcs)

        self.lexer = Lexer()
        self.parser = Parser()
        self.syntax = Env(init_syntax=True)

    def py_to_lisp_str(self, exp):
        '''
        Convert a Python object back into a Lisp-readable string for display.
        '''
        if isinstance(exp, RiplList):
            return '(' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        else:
            return str(exp)

    def eval(self, tkns, env):
        '''
        Try to evaluate an expression in an environment.
        NOTE: Special language features and syntax found here.
        '''
        # TODO: Break this into smaller, more testable chunks
        if not isinstance(tkns, list):  # constant literal
            try:
                # Check to see if we have this in the current environment.
                # NOTE: env.find returns the environment containing tkns.
                return env.find(RiplSymbol(tkns))[tkns]
            except AttributeError:
                # We bottomed out so return it raw
                return tkns
        elif tkns == RiplList():
            # got the emptylist
            return tkns
        else:                             # (proc arg...)
            call, *args = tkns
            try:
                exp = self.syntax.find(RiplSymbol(call))[call]
                return exp(args, self, env)
            except AttributeError:
                proc = self.eval(tkns[0], env)
                args = [self.eval(exp, env) for exp in tkns[1:]]
                return proc(*args)


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

    def eval_and_print(self, exp):
        '''
        Attempt to evaluate an expresion in an execution environment.
        Catches and displays output and exceptions.
        '''
        try:
            raw_tokens = self.lexer.get_tokens(exp)
            parsed_tokens = self.parser.parse(raw_tokens)
            val = self.eval(parsed_tokens, self.environment)
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
              '    Ctrl-Space to enter selection mode.\n'
              '    Ctrl-W/Y to cut/paste to system clipboard.\n'
              '    Ctrl-D to exit\n')

        history = InMemoryHistory()

        try:
            while True:
                user_input = prompt(
                        prompt_str,
                        history=history,
                        multiline=True,
                        wrap_lines=True,
                        mouse_support=True,
                        completer=self.completer,
                        enable_history_search=True,
                        clipboard=PyperclipClipboard(),
                        auto_suggest=AutoSuggestFromHistory())

                if user_input:
                    if user_input == 'quit':
                        exit_message()
                        break
                    else:
                        # Attempt to parse an expression and
                        # display any exceptions to the user.
                        self.eval_and_print(user_input)
        except (EOFError, KeyboardInterrupt):
            # User hit Ctl+d
            exit_message()
