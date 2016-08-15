'''
Classes that take unicode string input and run the
conversion from sexp -> python usable code.
'''
import re
from itertools import chain

from .bases import Symbol


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
        Tag(r'\`\(.+\)',                            'QUASI_QUOTED'),
        Tag(r'~(?P<p>[\(\[}]).+(?P=p)',             'CURRIED_SEXP'),
        Tag(r'\(,.+\)',                             'TUPLE'),
        Tag(r'(\(\)|\s*None)',                      'NULL'),
        Tag(r'\(',                                  'PAREN_OPEN'),
        Tag(r'\)',                                  'PAREN_CLOSE'),
        Tag(r'\[',                                  'BRACKET_OPEN'),
        Tag(r'\]',                                  'BRACKET_CLOSE'),
        Tag(r'{',                                   'BRACE_OPEN'),
        Tag(r'}',                                   'BRACE_CLOSE'),
        Tag(r'-?\d+\.\d+',                          'NUM_FLOAT'),
        Tag(r'-?\d+',                               'NUM_INT'),
        # TODO: add binary, ocal and hex?
        # base_prefixes = {"0b": 2, "0o": 8, "0x": 16}
        # for prefix, base in base_prefixes.items():
        #     if token.startswith(prefix):
        #         return int(token, base=base)
        Tag(r'"""([^"]*)"""',                       'DOCSTRING'),
        Tag(r'"([^"]*)"',                           'STRING'),
        # Need to check the closing but not consume it
        Tag(r'[^()[\]{}\s\#,\.]+(?=[\)\]}\s])?',    'SYMBOL'),
        Tag(r'\n',                                  'NEWLINE'),
        Tag(r'\s+',                                 'WHITESPACE'),
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
    else:
        return token.val


class Lexer:
    '''
    Breaks a string input into a python list of tokens.
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
            if lex_tag is 'NEWLINE':
                line_start = match.end()
                line_num += 1
            elif lex_tag in 'COMMENT COMMENT_SEXP WHITESPACE'.split():
                pass
            elif lex_tag == 'SYNTAX_ERROR':
                # There was something that we didn't recognise
                raise SyntaxError('Unable to parse: {}'.format(source_txt))
            elif lex_tag.startswith('QUOTED'):
                sub = '(quote ' + source_txt[1:] + ')'
                yield self.reglex(sub)
            elif lex_tag == 'QUASI_QUOTED':
                sub = '(quasiquote ' + source_txt[1:] + ')'
                yield self.reglex(sub)
            elif lex_tag == 'CURRIED_SEXP':
                sub = '(curry ' + source_txt[1:] + ')'
                yield self.reglex(sub)
            else:
                # Convert numerics now rather than in the parser
                if lex_tag == 'NUM_INT':
                    val = int(source_txt)
                elif lex_tag == 'NUM_FLOAT':
                    val = float(source_txt)
                else:
                    val = source_txt
                column = match.start() - line_start
                yield Token(lex_tag, val, line_num, column)


class Parser:
    '''
    Converts a stream of input tokens into a nested list of internal.
    '''
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
                sexp = []
                token = next(tokens)
                if token.tag == 'PAREN_CLOSE':
                    # Special case of the empty list
                    # TODO: make an object for this?
                    yield []
                else:
                    # Read until the end of the current s-exp
                    while token.tag != 'PAREN_CLOSE':
                        # De-sugar list literals
                        if token.tag == 'BRACKET_OPEN':
                            # discard the opening bracket
                            lst, tokens = self._parse_list(tokens)
                            sexp.append(lst)
                        # De-sugar dict literals the same way
                        elif token.tag == 'BRACE_OPEN':
                            dct, tokens = self._parse_dict(tokens)
                            sexp.append(dct)
                        else:
                            # Replace the token and pass everything through
                            # to check for nesting.
                            tokens = chain([token], tokens)
                            sexp.append(next(self.parse(tokens)))
                        # fetch the next token and loop
                        token = next(tokens)

                    # NOTE: implicitly dropping the final paren
                    yield sexp

            elif token.tag == 'PAREN_CLOSE':
                raise SyntaxError('unexpected ) in input')

            else:
                yield make_atom(token)

    def _parse_list(self, tokens):
        ''' :: gen(Token) -> List[], gen(Tokens)
        Parse a list literal all at once and return both the list and remaining
        tokens from the input stream.
            Note: This makes a list in memory and then passes it back to parse!
        '''
        tmp = []

        for token in tokens:
            while token.tag != 'BRACKET_CLOSE':
                tmp.append(token)
            # Drop the final bracket
            parsed = [v if type(v) == list else v for v in self.parse(tmp)]
            return ['(', 'quote', parsed, ')'], tokens
        # If we hit here then there was an error in the input.
        raise SyntaxError('missing closing ] in list literal')

    def _parse_dict(self, tokens):
        ''' :: gen(token) -> Dict{}, gen(Tokens)
        Parse a list literal and return the list and remaining tokens
        List literals are given as [...]
        '''
        tmp = []

        for token in tokens:
            while token.tag != 'BRACE_CLOSE':
                tmp.append(token)
            # NOTE: Dropping the final brace implicitly here

            parsed = [v if type(v) == list else v for v in self.parse(tmp)]

            if len(parsed) % 2 != 0:
                raise SyntaxError("Invalid dict literal")

            pairs = [parsed[i:i+2] for i in range(0, len(parsed), 2)]
            return {k: v for k, v in pairs}, tokens

        # If we hit here then there was an error in the input.
        raise SyntaxError('missing closing } in dict literal')
