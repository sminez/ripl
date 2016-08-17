'''
Classes that take unicode string input and run the
conversion from sexp -> python usable code.
'''
import re
from itertools import chain

from .bases import Symbol, Keyword, EmptyList, RList, RDict, RVector, RString


class Tag:
    '''A <pattern> -> <tag> mapping'''
    __slots__ = 'regex', 'tag'

    def __init__(self, regex, tag):
        self.regex = regex
        self.tag = tag


class Token:
    '''A tagged lexer token'''
    __slots__ = 'tag', 'val', 'line', 'col'

    def __init__(self, tag, val, line, col):
        self.tag = tag
        self.val = val
        self.line = line
        self.col = col

    def __eq__(self, other):
        return all((self.tag == other.tag, self.val == other.val,
                    self.line == other.line, self.col == other.col))


# TODO: Add pattern for complex numbers when we start supporting them
# NOTE: The SYMBOL tag is mad: "match anything not containing [stuff]
#       so long as it ends with [stuff].
RIPL_TAGS = [
        Tag(r';#\(.*\)',                            'COMMENT_SEXP'),
        Tag(r';.*\n?',                              'COMMENT'),
        Tag(r'\'\(.+\)',                            'QUOTED_SEXP'),
        Tag(r'\'.+(?=[\)\]}\s])?',                  'QUOTED_ATOM'),
        Tag(r'`\(.+\)',                             'QUASI_QUOTED'),
        Tag(r'~\(.+\)',                             'CURRIED_SEXP'),
        # Tag(r'\(,.+\)',                             'TUPLE'),
        Tag(r'(\(\)|\s*None)',                      'NULL'),
        # () {} []
        Tag(r'\(',                                  'PAREN_OPEN'),
        Tag(r'\)',                                  'PAREN_CLOSE'),
        Tag(r'\[',                                  'BRACKET_OPEN'),
        Tag(r'\]',                                  'BRACKET_CLOSE'),
        Tag(r'{',                                   'BRACE_OPEN'),
        Tag(r'}',                                   'BRACE_CLOSE'),
        # Numerics
        Tag(r'-?\d+\.?\d*[+-]\d+\.?\d*j',           'COMPLEX'),
        Tag(r'-?\d+\.?\d*j',                        'COMPLEX_PURE'),
        Tag(r'-?\d+\.\d+',                          'FLOAT'),
        Tag(r'-?0b[0-1]+',                          'INT_BIN'),
        Tag(r'-?0o[0-8]+',                          'INT_OCT'),
        Tag(r'-?0x[0-9a-fA-F]+',                    'INT_HEX'),
        Tag(r'-?\d+',                               'INT'),
        # Deliminators
        Tag(r',',                                   'COMMA'),
        Tag(r'\.',                                  'DOT'),
        Tag(r'\n',                                  'NEWLINE'),
        Tag(r'\s+',                                 'WHITESPACE'),
        # Strings
        Tag(r'"""([^"]*)"""',                       'DOCSTRING'),
        Tag(r'"([^"]*)"',                           'STRING'),
        Tag(r':[^()[\]{}\s\#,\.]+(?=[\)\]}\s])?',   'KEYWORD'),
        Tag(r'[^()[\]{}\s\#,\.]+(?=[\)\]}\s])?',    'SYMBOL'),
        Tag(r'.',                                   'SYNTAX_ERROR'),
        ]

_tags = '|'.join('(?P<{}>{})'.format(t.tag, t.regex) for t in RIPL_TAGS)
COMPILED_TAGS = re.compile(_tags)


def make_atom(token):
    ''' :: Token -> Symbol|Int|Float|String
    Strings and numbers are kept, every other token becomes a symbol.

    NOTE: This means that RIPL considers any custom classes a Symbol
          --> It would be nice to havea  type system here...
    '''
    if token.tag == 'SYMBOL':
        return Symbol(token.val)
    elif token.tag == 'KEYWORD':
        return Keyword(token.val)
    else:
        return token.val


class Reader:
    '''
    Breaks a string input into a python list of values.
    Double quoted string literals (including whitespace chars)
    are preserved as passed through as single tokens.

    TODO: Have an `update_syntax` function that is called by reader
          macros. Will need to work out where in the regex they get
          inserted...
    Maybe move them to first pass that just swaps things out if needed
    the same way as I'm currently handling quoting?
    '''
    def __init__(self):
        self.tags = COMPILED_TAGS

    def lex(self, string):
        ''' :: string -> gen(token)
        ```````````````````````````````````````````````````````````````````````
        Attempt to find and tag components of the user input using a master
        regular expression.
        NOTE:
            - tag / token definitions are at the top level of this module
              and are bound to the Lexer at initialisation.
            - The order of the regular expressions is important:
                - When we combine each individual tag into the master
                  `compiled_tags` expression, matches are found from left
                  to right. As such, tags earlier in the expression can
                  potentially clobber later tags!
                - We are using this in a couple of places:
                  - strings consisting of only [0-9] will become numerics
                    not symbols
                  - [Quasi]Quoted s-exps are matched before bare s-exps
            - Invalid expressions will raise a syntax error.
            - Comments get discarded and will not reach the parser.
            - S-expressions are recursively tokenized and nested into
              a single output list: [atom, atom, [atom, [atom, atom], atom]]
        '''
        int_bases = {'INT': 10, 'INT_BIN': 2, 'INT_OCT': 8, 'INT_HEX': 16}
        # Remove surrounding whitespace
        string = string.strip()

        if string.startswith('('):
            if not string.endswith(')'):
                raise SyntaxError('Unclosed s-expression in input')

        # tokens = []
        line_num = 1
        line_start = 0

        for match in re.finditer(self.tags, string):
            lex_tag = match.lastgroup
            # Take the selected version if we have it
            group = [g for g in match.groups() if g is not None]
            source_txt = group[1] if len(group) == 2 else match.group(lex_tag)
            if lex_tag == 'SYNTAX_ERROR':
                # There was something that we didn't recognise
                raise SyntaxError('Unable to parse: {}'.format(source_txt))
            elif lex_tag is 'NEWLINE':
                line_start = match.end()
                line_num += 1
            elif lex_tag in 'COMMENT COMMENT_SEXP WHITESPACE'.split():
                pass
            elif lex_tag.startswith('QUOTED'):
                sub = '(quote ' + source_txt[1:] + ')'
                for token in self.lex(sub):
                    yield token
            elif lex_tag == 'QUASI_QUOTED':
                sub = '(quasiquote ' + source_txt[1:] + ')'
                for token in self.lex(sub):
                    yield token
            elif lex_tag == 'CURRIED_SEXP':
                sub = '(curry ' + source_txt[1:] + ')'
                for token in self.lex(sub):
                    yield token
            else:
                # NOTE: We have something that we can convert to a value
                if lex_tag == 'NULL':
                    val = EmptyList()
                elif lex_tag in int_bases:
                    val = int(source_txt, int_bases[lex_tag])
                elif lex_tag == 'FLOAT':
                    val = float(source_txt)
                elif lex_tag.startswith('COMPLEX'):
                    val = complex(source_txt)
                    # regex groups need to be distinct so we differentiate
                    # above as a single regex is huge and an eyesore.
                    lex_tag = 'COMPLEX'
                else:
                    val = RString(source_txt)
                column = match.start() - line_start
                yield Token(lex_tag, val, line_num, column)

    def parse(self, tokens):
        ''' :: gen(Token) -> List[Symbol|String|int|float]
        ```````````````````````````````````````````````````````````````````````
        Converts a stream of tokens into a nested list of lists for evaluation.
        Tokens are a simple class with tag, val, line and col properties.
            Numerics are given the appropriate value in the Lexer.
            All other tags have a string as their value.

        LISPy (func arg1 arg2) lists become Pythonic ['func', 'arg1', 'arg2']
        '''
        if not tokens:
            # Can't run an empty program!
            raise SyntaxError('unexpected EOF while reading input')

        ################################################
        # NOTE: Need to be able to handle macros here! #
        ################################################
        # Something like:
        # token, tokens = self.apply_macros(token, tokens)
        for token in tokens:
            if token.tag == 'PAREN_OPEN':
                # Start of an s-expression, drop the intial paren
                token = next(tokens)
                sexp = []
                if token.tag == 'PAREN_CLOSE':
                    # Special case of the empty list
                    yield []  # EmptyList()
                else:
                    # Read until the end of the current s-exp
                    while token.tag != 'PAREN_CLOSE':
                        tokens = chain([token], tokens)
                        sexp.append(next(self.parse(tokens)))
                        token = next(tokens)
                    yield RList(sexp)
            elif token.tag == 'BRACKET_OPEN':
                # start of a vector literal, drop the initial bracket
                list_literal, tokens = self._parse_vector(tokens)
                yield list_literal
            elif token.tag == 'BRACE_OPEN':
                # start of a dict literal, drop the initial brace
                dict_literal, tokens = self._parse_dict(tokens)
                yield dict_literal

            elif token.tag in 'PAREN_CLOSE BRACKET_CLOSE BRACE_CLOSE'.split():
                warning = 'unexpected {} in input (line {} col {})'.format(
                        token.val, token.line, token.col)
                raise SyntaxError(warning)

            else:
                yield make_atom(token)

    def _parse_vector(self, tokens):
        ''' :: gen(Token) -> List[], gen(Tokens)
        Parse a vector literal all at once and return both the list and
        remaining tokens from the input stream.
            Note: This makes a list in memory and then passes it back to parse!
        '''
        tmp = []
        token = next(tokens)
        try:
            while token.tag != 'BRACKET_CLOSE':
                tmp.append(token)
                token = next(tokens)
            # Drop the final bracket
            parsed = RVector([v for v in self.parse(tmp)])
            return parsed, tokens
        except StopIteration:
            # If we hit here then there was an error in the input.
            raise SyntaxError('missing closing ] in list literal.')

    def _parse_dict(self, tokens):
        ''' :: gen(token) -> Dict{}, gen(Tokens)
        Parse a dict literal and return the dict and remaining tokens
        Dict literals are given as {k1 v1, k2 v2, ...}
        '''
        tmp = []
        token = next(tokens)
        try:
            while token.tag != 'BRACE_CLOSE':
                if token.tag != 'COMMA':
                    tmp.append(token)
                token = next(tokens)
            # Drop the final brace
            parsed = [v for v in self.parse(tmp)]
            if len(parsed) % 2 != 0:
                # We didn't get key/value pairs
                raise SyntaxError("Invalid dict literal")

            pairs = [parsed[i:i+2] for i in range(0, len(parsed), 2)]
            return RDict({k: v for k, v in pairs}), tokens
        except StopIteration:
            # If we hit here then there was an error in the input.
            raise SyntaxError('missing closing } in dict literal.')
