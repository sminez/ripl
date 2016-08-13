from unittest import TestCase
from ripl.backend import Lexer, Parser


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
