from pygments.token import Token
from pygments.lexer import RegexLexer, include, bygroups, words
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation

from pygments.lexers.python import PythonLexer
from pygments.styles.paraiso_dark import ParaisoDarkStyle
from prompt_toolkit.styles import style_from_pygments


#  Colour pallet
#  #383830 #49483e #75715e #a59f85 #d0c8c6
#  #e9e1dd #f9f8f5 #cb6077 #d28b71 #f4bc87
#  #beb55b #7bbda4 #8ab3b5 #a89bb9 #bb9584

ripl_style = style_from_pygments(ParaisoDarkStyle, {
        Token.Comment: '#75715e italic',
        Token.Punctuation.Quoted: '#a89bb9',
    })


class RiplLexer(RegexLexer):
    name = 'RIPL'
    aliases = ['Ripl']
    filenames = ['*.rpl']

    special_forms = (
        'car', 'cdr', 'import', 'do', 'is', 'in', 'eval',
        'quasiquote', 'unquote', 'unquote-splice', 'quote')

    declarations = 'define defn defmacro defclass lambda setv let'.split()

    builtins = (
        'define defn lambda if for-each quote yield yield-from'
        ' apply append begin car cdr cons not vector eq? equal?'
        ' callable? null? symbol? dict? tuple? list? vector?'
        ' int? float? number? complex? eval').split()

    # valid names for identifiers
    valid_name = r'(?!#)[\w!$%*+<=>?/.#-]+'

    def _multi_escape(entries):
        return words(entries, suffix=' ')

    tokens = {
        'root': [
            # the comments - always starting with semicolon
            # and going to the end of the line
            (r';.*$', Comment.Single),

            # whitespaces - usually not relevant
            (r'[,\s]+', Text),

            # numbers
            (r'-?\d+\.\d+', Number.Float),
            (r'-?\d+', Number.Integer),
            (r'0[0-7]+j?', Number.Oct),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),

            # strings, symbols and characters
            (r'"(\\\\|\\"|[^"])*"', String),
            (r"'" + valid_name, String.Symbol),
            (r"\\(.|[a-z]+)", String.Char),
            (r'^(\s*)([rRuU]{,2}"""(?:.|\n)*?""")',
                bygroups(Text, String.Doc)),
            (r"^(\s*)([rRuU]{,2}'''(?:.|\n)*?''')",
                bygroups(Text, String.Doc)),

            # keywords
            (r'::?' + valid_name, String.Symbol),

            # special operators
            (r'~@|`\'#^~&@', Operator),

            include('py-keywords'),
            include('py-builtins'),

            # highlight the special forms
            (_multi_escape(special_forms), Keyword),
            (_multi_escape(declarations), Keyword.Declaration),

            # highlight the builtins
            (_multi_escape(builtins), Name.Builtin),

            # the remaining functions
            (r'(?<=\()' + valid_name, Name.Function),

            # find the remaining variables
            (valid_name, Name.Variable),

            # list literals
            (r'(\[|\])', Punctuation),

            # dict literals
            (r'(\{|\})', Punctuation),

            # parentheses
            (r'(\(|\))', Punctuation),
            (r"'(\(|\))", Punctuation.Quoted),

        ],
        'py-keywords': PythonLexer.tokens['keywords'],
        'py-builtins': PythonLexer.tokens['builtins'],
    }

    def analyse_text(text):
        if '(import ' in text:
            return 0.9
