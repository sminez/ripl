import re
from unittest import TestCase

from ripl.bases import Symbol, RList
from ripl.backend import Reader, Token, make_atom


class LexerTest(TestCase):
    reader = Reader()

    def test_lex_tags(self):
        '''
        Individual tokens are correctly pulled out and in the correct order
        '''
        string = ('symbol ( ) [ ] { } 3.14 5 "string"'
                  ' """docstring""" () None'
                  ' 0b1010 0o172 0xab11'
                  ' -3j 2-2j 2.11j 3.14+1.59j 2-9.7j')
        tags = ('SYMBOL PAREN_OPEN PAREN_CLOSE'
                ' BRACKET_OPEN BRACKET_CLOSE BRACE_OPEN'
                ' BRACE_CLOSE FLOAT INT STRING'
                ' DOCSTRING NULL NULL'
                ' INT_BIN INT_OCT INT_HEX'
                ' COMPLEX COMPLEX COMPLEX COMPLEX COMPLEX').split()

        tokens = self.reader.lex(string)

        for token, tag in zip(tokens, tags):
            self.assertEqual(token.tag, tag)

    def test_dropped_tokens(self):
        '''
        Comments, comment sexps and whitespace do get matched but are dropped
        '''
        regex = self.reader.tags
        string = '\t ;#(discarded) \n ; all of this gets discarded\nkept'
        tokens = re.finditer(regex, string)
        tags = 'WHITESPACE COMMENT_SEXP WHITESPACE COMMENT SYMBOL'.split()

        for match, expected_tag in zip(tokens, tags):
            self.assertEqual(match.lastgroup, expected_tag)
        actual_tkns = self.reader.lex(string)
        token = next(actual_tkns)
        self.assertEqual(token, Token('SYMBOL', 'kept', 1, 45))
        # Confirm that that was the only token
        with self.assertRaises(StopIteration):
            token = next(actual_tkns)


class ParserTest(TestCase):
    reader = Reader()
    maxDiff = None

    def test_parse_no_tokens(self):
        '''parse raises a SyntaxError if it gets no tokens'''
        with self.assertRaises(SyntaxError):
            next(self.reader.parse(tokens=None))

    def test_parse_empty_list(self):
        '''The empty list gets parsed correctly and is equal to None'''
        string = '()'
        tokens = self.reader.lex(string)
        parsed = next(self.reader.parse(tokens))
        self.assertEqual(parsed, None)
        self.assertEqual(parsed, RList())

    def test_parse_simple(self):
        '''A simple s-expression gets parsed correctly'''
        string = '(print "foo" 1 3.14)'
        tokens = self.reader.lex(string)
        parsed = next(self.reader.parse(tokens))
        self.assertEqual(
                parsed,
                RList([Symbol('print'), 'foo', 1, 3.14])
                )

    def test_parse_nested(self):
        '''A nested s-expression gets parsed correctly'''
        string = '(print (+ "spam" " and eggs"))'
        _print = Symbol('print')
        _add = Symbol('+')
        tokens = self.reader.lex(string)
        parsed = next(self.reader.parse(tokens))
        self.assertEqual(
                parsed,
                RList([_print, RList([_add, 'spam', ' and eggs'])])
                )

    def test_parse_unclosed_sexp(self):
        '''An unclosed s-expression raises a syntax error'''
        with self.assertRaises(SyntaxError):
            string = '(this should fail'
            tokens = self.reader.lex(string)
            next(self.reader.parse(tokens))

    def test_parse_vector(self):
        '''Vector literals are correctly parsed'''
        string = '["this" "is" "a" "vector" "of" "strings"]'
        tokens = self.reader.lex(string)
        parsed = next(self.reader.parse(tokens))
        expected = ['this', 'is', 'a', 'vector', 'of', 'strings']
        self.assertEquals(parsed, expected)

    def test_parse_unclosed_vector(self):
        '''An unclosed vector raises a syntax error'''
        with self.assertRaises(SyntaxError):
            string = '[this should fail'
            tokens = self.reader.lex(string)
            next(self.reader.parse(tokens))

    def test_parse_dict(self):
        '''Dict literals are correctly parsed'''
        string = '{"a" 1, "b" 2, "c" 3}'
        tokens = self.reader.lex(string)
        parsed = next(self.reader.parse(tokens))
        expected = {"a": 1, "b": 2, "c": 3}
        self.assertEquals(parsed, expected)

    def test_parse_unclosed_dict(self):
        '''An unclosed dict raises a syntax error'''
        with self.assertRaises(SyntaxError):
            string = '{this should fail'
            tokens = self.reader.lex(string)
            next(self.reader.parse(tokens))


class AtomTest(TestCase):
    def test_make_atom(self):
        '''Tokens get parsed to the correct internal types'''
        token1 = make_atom(Token('SYMBOL', 'print', 0, 0))
        token2 = make_atom(Token('STRING', 'foo', 0, 0))
        token3 = make_atom(Token('INT', 1, 0, 0))
        token4 = make_atom(Token('FLOAT', 3.14, 0, 0))
        self.assertEqual(type(token1), Symbol)
        self.assertEqual(type(token2), str)
        self.assertEqual(type(token3), int)
        self.assertEqual(type(token4), float)
