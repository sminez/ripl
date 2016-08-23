import sys
import traceback
from collections import Container, Counter

from pygments.token import Token

from prompt_toolkit.keys import Keys
from prompt_toolkit.document import Document
from prompt_toolkit.filters import IsDone, Filter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.layout.processors import \
    ConditionalProcessor, HighlightMatchingBracketProcessor
from prompt_toolkit.shortcuts import \
        create_prompt_application, create_output, create_eventloop

from ripl.backend import Reader
from ripl.bases import Symbol, EmptyList, RList, Func, nested_scope, Scope
from ripl.repl_utils import RiplLexer, ripl_style
from ripl.bases import get_global_scope

import ripl.prelude as prelude


def is_balanced(text):
    '''Check that () {} [] are all matched'''
    c = Counter(text)
    return all([c['('] == c[')'], c['{'] == c['}'], c['['] == c[']']])


class ParenValidator(Validator):
    '''
    Check that the input has balanced parens/brackets/braces
    '''
    def validate(self, document):
        balanced = is_balanced(document.text)
        if not balanced:
            raise ValidationError(
                message='Unclosed expression in input',
                cursor_position=len(document.text))


class Tab_to_whitespace(Filter):
    '''
    Insert whitespace rather than autocomplete when there is nothing
    to complete.
    '''
    def __call__(self, cli):
        b = cli.current_buffer
        before_cursor = b.document.current_line_before_cursor

        return b.text and (not before_cursor or before_cursor.isspace())


def newline_and_indent(buf):
    '''Insert a new line and handle indenting based on input so far'''
    if buf.document.current_line_after_cursor:
        # Cursor is in the middle of a line: always insert a new line
        buf.insert_text('\n')
    else:
        # Cursor is at the end of a line so add a new line and
        # work out how far we need to indent.
        buf.insert_text('\n')
        # If we are indenting, we are unbalanced so find out
        # how many open expressions are in the current buffer.
        indent = 0
        c = Counter(buf.document.text)
        indent += (c.get('(', 0) - c.get(')', 0))
        indent += (c.get('[', 0) - c.get(']', 0))
        indent += (c.get('{', 0) - c.get('}', 0))
        buf.insert_text('  ' * indent)


class Evaluator:
    '''
    Base class for the Ripl interpretor and Ripl transpiler.
        Not sure whether to call it a compiler or not as it
        should eventually be able to output .py and .pyc
    '''
    def __init__(self, use_prelude=True):
        self.global_scope = get_global_scope()
        if use_prelude:
            funcs = {Symbol(k): v for k, v in vars(prelude).items()}
            self.global_scope.update(funcs)

        self.reader = Reader()
        self.syntax = Scope()

    def py_to_lisp_str(self, exp):
        '''
        Convert a Python object back into a Lisp-readable string for display.
        NOTE: Not referencing internal types here as we need interopt with
              other Python code.
        '''
        if isinstance(exp, RList):
            # (1 2 ... n)
            return str(exp)
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
        while True:
            if isinstance(tkns, RList):
                # Internal representation of an s-expression
                if tkns == EmptyList():
                    return EmptyList()
                elif isinstance(tkns[0], Container):
                    if len(tkns) == 2:
                        # Containers are functions of Key/Index -> value so
                        # we allow calling them as syntax for `get`
                        # (<CONTAINER> KEY/INDEX) -> VALUE
                        if isinstance(tkns[0], RList):
                            if tkns[0][0] == Symbol('quote'):
                                raise SyntaxError(
                                        'Cannot index into quoted list')
                        return tkns[0].__getitem__(tkns[1])
                    else:
                        raise SyntaxError('Invalid function call')
                else:
                    # This is a call
                    # NOTE: This args always a list:
                    #       (foo 1 2 3)   -> foo, [1,2,3]
                    #       (foo 1)       -> foo, [1]
                    #       (foo (1 2 3)) -> foo, [(1,2,3)]
                    call, *args = tkns

                    if call == Symbol('quote'):
                        # Return the argument without evaluation
                        return args[0]
                    elif call == Symbol('quasiquote'):
                        # TODO: check that this works!
                        # Splice is unquoted args and then return
                        # without evaluating
                        exp = args[0]
                        if len(exp) == 1:
                            return exp  # [Symbol('quote'), args[0]]
                        else:
                            rep = []
                            iter_exp = iter(exp)
                            for element in iter_exp:
                                if element == Symbol('~'):
                                    # Unquote s-expression
                                    unquoted = next(iter_exp)
                                    rep.append(self.eval(unquoted, scope))
                                elif element == Symbol('~@'):
                                    # Unquote and splice s-expression
                                    unquoted = next(iter_exp)
                                    try:
                                        expression = self.eval(unquoted, scope)
                                    except TypeError:
                                        expression = unquoted
                                    if not isinstance(expression, RList):
                                        raise SyntaxError(
                                            'Can only use ~@ on an expression')
                                    for atom in expression:
                                        rep.append(atom)
                                else:
                                    rep.append(element)
                            return RList(rep)
                    elif call == Symbol('define'):
                        # Attempt to define a new symbol, fails if the
                        # symbol is already defined
                        name, expression = args
                        if scope.get(name):
                            raise SyntaxError(
                                    'use set! to modify a stored symbol')
                        scope[name] = self.eval(expression, scope)
                        return None
                    elif call == Symbol('defn'):
                        # (defn foo
                        #  """do that voodoo that foo do"""
                        #  (body ...))
                        # handle function definitions
                        if len(args) == 4:
                            docstring = args.pop(1)
                        else:
                            docstring = None
                        name, args, body = args
                        scope[name] = Func(args, docstring, body, scope, self)
                        return None
                    elif call == Symbol('defmacro'):
                        # handle macro definitions
                        raise SyntaxError("haven't finished macros!")
                    elif call == Symbol('set'):
                        # dame as define but allow mutation
                        name, expression = args
                        scope[name] = self.eval(expression, scope)
                        return None
                    elif call == Symbol('if'):
                        # handle both forms of if
                        # if/elif... will be replaced with a cond macro
                        if len(args) == 3:
                            test, _true, _false = args
                        elif len(args) == 2:
                            test, _true = args
                            _false = None
                        tkns = _true if self.eval(test, scope) else _false
                    elif call == Symbol('eval'):
                        # evaluate a quoted expression
                        tokens = args[0]
                        if isinstance(tokens, list):
                            # tokens are [quote, [ ... ]]
                            return self.eval(tokens[1], scope)
                        else:
                            # single token is a symbol, try to look it up
                            try:
                                _val = scope[tokens]
                            except AttributeError:
                                raise NameError(
                                    'undefined symbol {}'.format(tokens)
                                    )
                            tkns = self.eval(_val, scope)
                    elif call == Symbol('lambda'):
                        # make a procedure
                        bindings, body = args
                        return Func(bindings, 'anonymous lambda', body,
                                    scope, self)
                    else:
                        func, *arg_vals = tkns
                        proc = self.eval(func, scope)
                        args = [self.eval(exp, scope) for exp in arg_vals]
                        if isinstance(proc, Func):
                            # A ripl Func with a body we can extract to allow
                            # tail calls
                            tkns = proc.body
                            scope = nested_scope(proc.scope, proc.args, args)
                        else:
                            # Evaluate
                            return proc(*args)
            else:
                # This is an atom: a symbol or a built-in type
                # Check to see if we have it in the current scope.
                try:
                    return scope[tkns]
                except KeyError:
                    # We just tried to perform lookup on None:
                    # --> tkns is not a known symbol
                    if isinstance(tkns, Symbol):
                        raise NameError(
                                 'symbol {} is not defined'.format(tkns))
                    else:
                        # It's a value
                        return tkns


class REPL(Evaluator):
    completions = (
            'define defn lambda if for-each quote yield yield-from'
            ' apply append begin car cdr cons not vector eq? equal?'
            ' callable? null? symbol? dict? tuple? list? vector?'
            ' int? float? number? complex? eval').split()
    completions.extend([
            'getattr', 'str', 'property', 'license', 'divmod', 'object',
            'issubclass', 'all', 'exit', 'None', 'format', 'set', 'slice',
            'max', 'complex', 'chr', 'id', 'reversed', 'SystemExit', 'hex',
            'True', 'type', 'len', 'open', 'bool', 'dict', 'next', 'bytes',
            'Exception', 'min', 'hasattr', 'range', 'Ellipsis', 'any',
            'abs', 'round', 'compile', 'quit', 'staticmethod', 'float',
            'eval', 'credits', 'exec', 'memoryview', 'delattr', 'dir',
            'ord', 'print', 'callable', 'bytearray', 'sum', 'bin',
            'frozenset', 'StopAsyncIteration', 'vars', 'repr', 'globals',
            'oct', 'pow', 'sorted', 'tuple', 'filter', 'isinstance', 'int',
            'zip', 'setattr', 'input', 'help', 'hash', 'enumerate',
            'False', 'locals', 'list', 'map', 'ascii', 'super', 'iter'
            ])

    def cont_tokens(self, cli, width):
        '''For use with multiline input when I get that working...'''
        return [(Token, '~' * (width - 1) + ' ')]

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
        except StopIteration:
            pass
        except:
            excinf = sys.exc_info()
            sys.last_type, sys.last_value, last_tb = excinf
            sys.last_traceback = last_tb
            try:
                lines = traceback.format_exception(
                        excinf[0],
                        excinf[1],
                        last_tb.tb_next)
                print(''.join(lines), file=sys.stderr)
            finally:
                last_tb, excinf = None, None

    def read(self, prompt_str='λ く'):
        '''
        The main read eval print loop for RIPL.
        Uses prompt_toolkit:
            http://python-prompt-toolkit.readthedocs.io/en/stable/
        '''
        def exit_message():
            print('\nThanks for giving RIPL a try!\nさようなら!\n')

        if not self.global_scope:
            raise EnvironmentError('Things have gone horribly wrong...')

        print(' <({[ RIPL -- RIPL Is Pythonic Lisp ]})>\n'
              '    Ctrl-Space to enter selection mode.\n'
              '    Ctrl-W/Y to cut/paste to system clipboard.\n'
              '    Ctrl-D to exit\n')

        history = InMemoryHistory()
        completer = WordCompleter(self.completions, ignore_case=True)
        kbm = KeyBindingManager.for_prompt(enable_system_bindings=True)
        add_binding = kbm.registry.add_binding

        @add_binding(Keys.Tab, filter=Tab_to_whitespace())
        def _(event):
            '''Either indent or do completion'''
            event.cli.current_buffer.insert_text('  ')

        @add_binding(Keys.ControlJ)
        def __(event):
            '''Either enter a newline or accept input based on context'''
            b = event.current_buffer
            txt = b.document.text

            def at_end(b):
                '''Is the cursor at the end of the buffer?'''
                text = b.document.text_after_cursor
                return text == '' or (text.isspace() and '\n' not in text)

            at_end = at_end(b)
            has_empty_line = txt.replace(' ', '').endswith('\n')
            balanced = is_balanced(b.document.text)
            if (at_end and has_empty_line) or balanced:
                if b.validate():
                    b.accept_action.validate_and_handle(event.cli, b)
            else:
                newline_and_indent(b)

        # Show matching parentheses, but only while editing.
        highlight_parens = ConditionalProcessor(
            processor=HighlightMatchingBracketProcessor(
                chars='[](){}'),
            filter=~IsDone())

        while True:
            repl = create_prompt_application(
                    prompt_str,
                    multiline=True,
                    history=history,
                    style=ripl_style,
                    mouse_support=True,
                    completer=completer,
                    validator=ParenValidator(),
                    enable_history_search=True,
                    complete_while_typing=False,
                    clipboard=PyperclipClipboard(),
                    lexer=PygmentsLexer(RiplLexer),
                    key_bindings_registry=kbm.registry,
                    display_completions_in_columns=True,
                    auto_suggest=AutoSuggestFromHistory(),
                    get_continuation_tokens=self.cont_tokens,
                    extra_input_processors=[highlight_parens])

            try:
                eventloop = create_eventloop()
                cli = CommandLineInterface(
                    application=repl,
                    eventloop=eventloop,
                    output=create_output(true_color=True))

                user_input = cli.run(reset_current_buffer=False)
                if user_input:
                    if isinstance(user_input, Document):
                        user_input = user_input.text
                    lines = user_input.split('\n')
                    expression = ' '.join([l.strip() for l in lines])
                    self.eval_and_print(expression)
            except (EOFError, KeyboardInterrupt):
                # User hit Ctl+d
                exit_message()
                break
            finally:
                eventloop.close()
