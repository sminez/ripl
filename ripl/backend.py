'''
Classes that take unicode string input and run the
conversion from sexp -> python usable code.
'''
from .types import RiplSymbol, RiplString
from .types import RiplInt, RiplFloat


class Lexer:
    '''
    Breaks a string input into a python list of tokens.
    Double quoted string literals (including whitespace chars)
    are preserved as passed through as single tokens.
    '''
    def get_tokens(self, string):
        '''
        Find string literals and preserve them while breaking
        the rest of the input into individual tokens.
        '''
        if '"' not in string:
            return self.tokenize(string)
        else:
            if string.count('"') % 2 != 0:
                raise SyntaxError('Unclosed string literal in input')
            else:
                tokens = []
                index_1 = string.find('"')
                start = string[:index_1]
                rest = string[index_1:]
                # Break everything up until the start of the string
                # literal into tokens
                tokens += self.tokenize(start)
                index_2 = rest[1:].find('"')
                # Add the string literal as its own token
                tokens.append(rest[:index_2 + 2])
                # Break the rest of the input into tokens while
                # still checking for other string literals.
                tokens += self.get_tokens(rest[index_2 + 2:])
                return tokens

    def tokenize(self, input_string):
        '''
        Convert a string into a list of tokens.
        Pads parens/braces/brackets with whitespace for stripping.
        '''
        tokens = input_string.replace('(', ' ( ').replace(')', ' ) ')
        tokens = tokens.replace('[', ' [ ').replace(']', ' ] ')
        tokens = tokens.replace('{', ' { ').replace('}', ' } ')
        return tokens.split()


class Parser:
    '''
    Converts a python list of input tokens into executable python code.
    '''
    def parse(self, tokens):
        '''
        Read an expression from a sequence of tokens.
        Converts LISPy (func arg1 arg2) to Pythonic ['func', 'arg1', 'arg2']
        Nesting works as expected and other datastructures get passed through:
        {:key1 val1 :key2 val2} -> ['{', ':key1', 'val1', ':key2', 'val2', '}']
        [val1 val2 val3] -> ['[', 'val1', 'val2', 'val3', ']']

        The dict example above is following the syntax from clojure and
        explicitly marks keys using the : operator. Need to allow arbitrary
        key types so things like:
            :"string", :42, :Function
        should all work
        '''
        # NOTE: Python tuples wont work with this...!
        # TODO: (, 1 2 3) -> (1, 2, 3) i.e. have ',' map to 'tuple'
        if not tokens:
            # Can't run an empty program!
            raise SyntaxError('unexpected EOF while reading input')

        # Grab the first token
        token = tokens.pop(0)

        if token == '(':
            try:
                # Start of an sexp, drop the intial paren
                sexp = []
                while tokens[0] != ')':
                    # NOTE: BROKEN HERE!
                        sexp.append(self.parse(tokens))
                # drop the final paren as well
                tokens.pop(0)
                return sexp
            except IndexError:
                raise SyntaxError('missing closing )')
        elif token == ')':
            raise SyntaxError('unexpected ) in input')
        else:
            return self.atom(token)

    def atom(self, token):
        '''
        Numbers become numbers; every other token is a symbol.
        NOTE: only double quotes denote strings
              will be using single quotes for quoting later.
        --> String literals are handled in read_from_tokens.
        '''
        # TODO: other numeric types, bytes
        if token.startswith('"') and token.endswith('"'):
            return RiplString(token[1:-1])
        try:
            return RiplInt(token)
        except ValueError:
            try:
                return RiplFloat(token)
            except ValueError:
                return RiplSymbol(token)
