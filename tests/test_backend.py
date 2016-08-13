from unittest import TestCase

from ripl.bases import Symbol
from ripl.backend import Lexer, Parser, make_atom


class LexerTest(TestCase):
    lexer = Lexer()

    def test_tokenize(self):
        '''Input gets broken into the correct tokens.'''
        string = '(print 1 2 3)'
        tokens = self.lexer.tokenize(string)
        self.assertEquals(tokens, ['(', 'print', '1', '2', '3', ')'])

    def test_get_tokens(self):
        '''Strings get tokenized correctly'''
        string = '(print "this" " and that")'
        tokens = self.lexer.get_tokens(string)
        self.assertEquals(tokens, ['(', 'print', '"this"', '" and that"', ')'])


class ParserTest(TestCase):
    lexer = Lexer()
    parser = Parser()

    def test_parse_simple(self):
        '''A simple sexp gets parsed correctly'''
        string = '(print "foo" 1 3.14)'
        tokens = self.lexer.get_tokens(string)
        parsed = self.parser.parse(tokens)
        self.assertEquals(parsed, ['print', 'foo', 1, 3.14])

    def test_parse_nested(self):
        '''A nested sexp gets parsed correctly'''
        string = '(print (+ "spam" " and eggs"))'
        tokens = self.lexer.get_tokens(string)
        parsed = self.parser.parse(tokens)
        self.assertEquals(parsed, ['print', ['+', 'spam', ' and eggs']])


class AtomTest(TestCase):
    def test_make_atom(self):
        '''Tokens get parsed to the correct internal types'''
        token1 = make_atom('print')
        token2 = make_atom('"foo"')
        token3 = make_atom('1')
        token4 = make_atom('3.14')
        self.assertEqual(type(token1), Symbol)
        self.assertEqual(type(token2), str)
        self.assertEqual(type(token3), int)
        self.assertEqual(type(token4), float)
