from pygments.token import Token
from prompt_toolkit.layout.lexers import PygmentsLexer

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

from prompt_toolkit.layout.processors import ConditionalProcessor, \
        HighlightMatchingBracketProcessor
from prompt_toolkit.filters import IsDone


from .bases import Env, Symbol
from .backend import Lexer, Parser
from .repl_utils import RiplLexer, ripl_style

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
            funcs = {Symbol(k): v for k, v in vars(prelude).items()}
            self.environment.update(funcs)

        self.lexer = Lexer()
        self.parser = Parser()
        self.syntax = Env(init_syntax=True)

    def py_to_lisp_str(self, exp):
        '''
        Convert a Python object back into a Lisp-readable string for display.
        '''
        if isinstance(exp, list):
            # (1 2 ... n)
            return '(' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        if isinstance(exp, dict):
            # {a 1, b 2, ... k v}
            tmp = ['{} {}'.format(k, v) for k, v in exp.items()]
            return '{' + ', '.join(tmp) + '}'
        if isinstance(exp, tuple):
            # (, 1 2 ... n)
            return '(,' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        else:
            return str(exp)

    def eval(self, tkns, env):
        '''
        Try to evaluate an expression in an environment.
        NOTE: Special language features and syntax found here.
        '''
        if not isinstance(tkns, list):
            # This is an atom: a symbol or a built-in type
            try:
                # Check to see if we have this in the current environment.
                # NOTE: env.find returns the environment containing tkns.
                return env.find(Symbol(tkns))[tkns]
            except AttributeError:
                # This is not a known symbol
                if isinstance(tkns, Symbol):
                    raise NameError('symbol {} is not defined'.format(tkns))
                else:
                    return tkns
        elif tkns == []:
            # got the emptylist
            return tkns
        else:                             # (proc arg...)
            call, *args = tkns
            try:
                exp = self.syntax.find(Symbol(call))[call]
                return exp(args, self, env)
            except AttributeError:
                proc = self.eval(tkns[0], env)
                args = [self.eval(exp, env) for exp in tkns[1:]]
                return proc(*args)


class RiplRepl(RiplExecutor):
    def __init__(self, debug=False):
        self.debug = debug
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
            if self.debug:
                # Allow analysis of traceback
                # NOTE: crashes the repl!
                raise e

    def repl(self, prompt_str='λ く'):
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

        # Show matching parentheses, but only while editing.
        highlight_parens = ConditionalProcessor(
            processor=HighlightMatchingBracketProcessor(chars='[](){}'),
            filter=~IsDone())

        try:
            while True:
                user_input = prompt(
                        prompt_str,
                        style=ripl_style,
                        lexer=PygmentsLexer(RiplLexer),
                        extra_input_processors=[highlight_parens],
                        history=history,
                        # multiline=True,
                        mouse_support=True,
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
