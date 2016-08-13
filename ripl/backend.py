'''
Classes that take unicode string input and run the
conversion from sexp -> python usable code.
'''
from .bases import Symbol


def make_atom(token):
    '''
    Strings and numbers are kept, every other token becomes a symbol.
    NOTE: only double quotes denote strings
          will be using single quotes for quoting later.
    --> String literals are handled in read_from_tokens.
    '''
    # TODO: other numeric types, bytes
    if token.startswith('"') and token.endswith('"'):
        return str(token[1:-1])
    else:
        try:
            return int(token)
        except ValueError:
            try:
                # See if we have a valid bin/oct/hex
                base_prefixes = {"0b": 2, "0o": 8, "0x": 16}
                for prefix, base in base_prefixes.items():
                    if token.startswith(prefix):
                        return int(token, base=base)
                raise ValueError
            except ValueError:
                try:
                    return float(token)
                except ValueError:
                    return Symbol(token)


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
        # Allow for the parsing of quoted atoms
        tokens = tokens.replace("'", " ' ")
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
                    return []

                # Read until the end of the current s-exp
                while tokens[0] != ')':
                    # De-sugar list literals
                    if tokens[0] == '[':
                        tokens.pop(0)
                        lst, tokens = self._parse_list_literal(tokens)
                        sexp.append(lst)
                        if tokens[0] == ')':
                            # The list literal was at the end of the s-exp
                            return sexp
                        else:
                            # Keep parsing!
                            sexp.append(self.parse(tokens))
                    # De-sugar dict literals the same way
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
            return make_atom(token)

    def _parse_list_literal(self, tokens):
        '''
        Parse a list literal and return the list and remaining tokens
        List literals are given as [...]
        '''
        lst = []

        try:
            while tokens[0] != ']':
                lst.append(self.parse(tokens))
            # drop the final bracket
            tokens.pop(0)
            return ['(', 'quote', lst, ')'], tokens

        except IndexError:
            raise SyntaxError('missing closing ] in list literal')

    def _parse_dict_literal(self, tokens):
        '''
        Parse a list literal and return the list and remaining tokens
        List literals are given as [...]
        '''
        tmp = []

        try:
            while tokens[0] != '}':
                tmp.append(self.parse(tokens))
            # drop the final brace
            tokens.pop(0)

            if len(tmp) % 2 != 0:
                raise SyntaxError("Invalid dict literal")

            pairs = [tmp[i:i+2] for i in range(0, len(tmp), 2)]
            return {k: v for k, v in pairs}, tokens

        except IndexError:
            raise SyntaxError('missing closing } in dict literal')

    def apply_quote(self, tokens):
        '''
        We found a ' in the input so we need to quote either the next
        s-expression or the next atom.
            '<atom>    --> (quote <atom>)
            '(<s-exp>) --> (quote (<s-exp>))
        '''
        if tokens[0] not in ['(', '{']:
            # Got a quoted atom
            return ['(', 'quote', tokens[0], ')'] + tokens[1:]
        elif tokens[0] == '(':
            # Got a quoted s-expression
            deliminator = ')'
        elif tokens[0] == '{':
            # Got a quoted dict literal
            deliminator = '}'

        quoted = ['(', 'quote']
        token = tokens.pop(0)
        while token != deliminator:
            quoted.append(token)
            token = tokens.pop(0)

        # Add the closing parens for the s-expression and the quote
        quoted.append(token)

        return quoted + [')'] + tokens
