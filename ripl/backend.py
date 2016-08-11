'''
Classes that take unicode string input and run the
conversion from sexp -> python usable code.
'''
from .types import RiplSymbol, RiplString, RiplList, RiplDict
from .types import RiplInt, RiplFloat


class Lexer:
    '''
    Breaks a string input into a python list of tokens.
    Double quoted string literals (including whitespace chars)
    are preserved as passed through as single tokens.
    '''
    def get_tokens(self, string):
        '''
        Find string literals and preserve whitespace in them while
        breaking the rest of the input into individual tokens.
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

    def tokenize(self, string):
        '''
        Convert a string into a list of tokens.
        Pads parens/braces/brackets with whitespace for stripping.
        '''
        tokens = string.replace('(', ' ( ').replace(')', ' ) ')
        tokens = tokens.replace('[', ' [ ').replace(']', ' ] ')
        tokens = tokens.replace('{', ' { ').replace('}', ' } ')
        return tokens.split()

    # NOTE: this probably wont work as it won't allow for nesting :(
    # def get_list_from_str(self, string):
    #     start, _, rest = string.partition('[')
    #     body, _, end = rest.rpartition(']')
    #     return start, '[' + body + ']', end

    # def get_dict_from_str(self, string):
    #     start, _, rest = string.partition('{')
    #     body, _, end = rest.rpartition('}')
    #     return start, '{' + body + '}', end


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
        if not tokens:
            # Can't run an empty program!
            raise SyntaxError('unexpected EOF while reading input')

        #################################################
        # NOTE: Need to be able to handle reader macros #
        #################################################
        # Something like:
        # token, tokens = self.apply_reader_macros(token, tokens)

        if tokens[0] == "'":
            tokens.pop(0)
            tokens = self.apply_quote(tokens)

        # Grab the first token
        token = tokens.pop(0)

        ################################################
        # NOTE: Need to be able to handle macros here! #
        ################################################
        # Something like:
        # token, tokens = self.apply_macros(token, tokens)

        if token == '(':
            try:
                # Start of an s-exp, drop the intial paren
                sexp = []
                if tokens[0] == ')':
                    # Special case of the empty list
                    tokens.pop(0)
                    return RiplList()

                while tokens[0] != ')':
                    if tokens[0] == '[':
                        tokens.pop(0)
                        lst, tokens = self._parse_list_literal(tokens)
                        sexp.append(lst)
                        if tokens[0] == ')':
                            return sexp
                        else:
                            sexp.append(self.parse(tokens))
                    elif tokens[0] == '{':
                        tokens.pop(0)
                        dct, tokens = self._parse_dict_literal(tokens)
                        sexp.append(dct)
                        if tokens[0] == ')':
                            return sexp
                        else:
                            sexp.append(self.parse(tokens))
                    else:
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
        else:
            try:
                return RiplInt(token)
            except ValueError:
                try:
                    return RiplFloat(token)
                except ValueError:
                    return RiplSymbol(token)

    def _parse_list_literal(self, tokens):
        '''
        Parse a list literal and return the list and remaining tokens
        List literals are given as [...]
        '''
        tmp = []

        try:
            while tokens[0] != ']':
                tmp.append(self.parse(tokens))
            # drop the final bracket
            tokens.pop(0)
            return RiplList(tmp), tokens

        except IndexError:
            raise SyntaxError('missing closing ] in list literal')

    def _parse_dict_literal(self, tokens):
        '''
        Parse a list literal and return the list and remaining tokens
        List literals are given as [...]
        '''
        tmp = []
        key = True

        try:
            while tokens[0] != '}':
                if key:
                    if not tokens[0].startswith(':'):
                        raise SyntaxError("Invalid dict literal")
                    # Drop leading : from keys
                    tokens[0] = tokens[0][1:]
                    key = False
                else:
                    key = True
                tmp.append(self.parse(tokens))
            # drop the final brace
            tokens.pop(0)

            if len(tmp) % 2 != 0:
                raise SyntaxError("Invalid dict literal")
            return RiplDict(tmp), tokens

        except IndexError:
            raise SyntaxError('missing closing } in dict literal')

    def apply_quote(self, tokens):
        '''
        We found a ' in the input so we need to quote either the next
        s-expression or the next atom.
            '<atom>    --> (quote <atom>)
            '(<s-exp>) --> (quote (<s-exp>))
        '''
        if tokens[0] == '(':
            # Got a quoted s-expression
            quoted = ['(', 'quote', ]
            token = tokens.pop(0)
            while token != ')':
                quoted.append(token)
                token = tokens.pop(0)
            # Add the closing parens for the s-expression and the quote
            quoted += [token, ')']
            return quoted + tokens
        else:
            # Got a quoted atom
            return ['(', 'quote', tokens[0], ')'] + tokens[1:]
