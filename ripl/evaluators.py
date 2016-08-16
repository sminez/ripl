from pygments.token import Token
from prompt_toolkit.layout.lexers import PygmentsLexer

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard

from prompt_toolkit.filters import IsDone
from prompt_toolkit.layout.processors import \
    ConditionalProcessor, HighlightMatchingBracketProcessor

from collections import deque

from .backend import Reader
from .bases import Scope, Symbol, RList, EmptyList
from .repl_utils import RiplLexer, ripl_style

import ripl.prelude as prelude


class RiplEvaluator:
    '''
    Base class for the Ripl interpretor and Ripl transpiler.
        Not sure whether to call it a compiler or not as it
        should eventually be able to output .py and .pyc
    '''
    def __init__(self, use_prelude=True):
        self.global_scope = Scope(use_standard=True)
        if use_prelude:
            funcs = {Symbol(k): v for k, v in vars(prelude).items()}
            self.global_scope.update(funcs)

        self.reader = Reader()
        self.syntax = Scope(init_syntax=True)

    def py_to_lisp_str(self, exp):
        '''
        Convert a Python object back into a Lisp-readable string for display.
        NOTE: Not referencing internal types here as we need interopt with
              other Python code.
        '''
        if isinstance(exp, deque):
            # (1 2 ... n)
            return '(' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        elif isinstance(exp, list):
            # [1 2 ... n]
            return '[' + ' '.join(map(self.py_to_lisp_str, exp)) + ']'
        elif isinstance(exp, dict):
            # {a 1, b 2, ... k v}
            tmp = ['{} {}'.format(k, v) for k, v in exp.items()]
            return '{' + ', '.join(tmp) + '}'
        elif isinstance(exp, tuple):
            # (, 1 2 ... n)
            return '(,' + ' '.join(map(self.py_to_lisp_str, exp)) + ')'
        else:
            return str(exp)

    def eval(self, tkns, scope):
        '''
        Try to evaluate an expression in a given scope.
        NOTE: Special language features and syntax found here.
        '''
        if not isinstance(tkns, RList):
            # This is an atom: a symbol or a built-in type
            # Check to see if we have it in the current scope.
            try:
                return scope[tkns]
            except KeyError:
                # We just tried to perform lookup on None:
                # --> tkns is not a known symbol
                if isinstance(tkns, Symbol):
                    raise NameError('symbol {} is not defined'.format(tkns))
                else:
                    # It's a value
                    return tkns
        elif tkns == EmptyList():
            # Empty list
            return EmptyList()
        else:
            call, *args = tkns
            try:
                # See if this is a known piece of syntax
                builtin = self.syntax[call]
                return builtin(args, self, scope)
            except KeyError:
                func, *arg_vals = tkns
                proc = self.eval(func, scope)
                args = [self.eval(exp, scope) for exp in arg_vals]
                return proc(*args)


class RiplRepl(RiplEvaluator):
    def __init__(self, debug=False):
        self.debug = debug
        super().__init__()

    def get_continuation_tokens(self, cli, width):
        '''For use with multiline input when I get that working...'''
        return [(Token, '~' * width)]

    def eval_and_print(self, exp):
        '''
        Attempt to evaluate an expresion in an execution scope.
        Catches and displays output and exceptions.
        '''
        try:
            raw_tokens = self.reader.lex(exp)
            parsed_tokens = next(self.reader.parse(raw_tokens))
            val = self.eval(parsed_tokens, self.global_scope)
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

        if not self.global_scope:
            raise EnvironmentError('Things have gone horribly wrong...')

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
