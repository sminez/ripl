import re
from unittest import TestCase

from ripl.bases import Symbol
from ripl.backend import Lexer, Token, Parser, make_atom


class LexerTest(TestCase):
    lexer = Lexer()

    def test_reglex_tags(self):
        '''
        Individual tokens are correctly pulled out and in the correct order
        '''
        string = ('symbol ( ) [ ] { } 3.14 5 "string"'
                  ' """docstring""" () None')
        tags = ('SYMBOL PAREN_OPEN PAREN_CLOSE'
                ' BRACKET_OPEN BRACKET_CLOSE BRACE_OPEN'
                ' BRACE_CLOSE NUM_FLOAT NUM_INT STRING'
                ' DOCSTRING NULL NULL').split()

        tokens = self.lexer.lex(string)

        for token, tag in zip(tokens, tags):
            self.assertEqual(token.tag, tag)

    def test_dropped_tokens(self):
        '''
        Comments, comment sexps and whitespace do get matched but are dropped
        '''
        regex = self.lexer.tags
        string = '\t ;#(discarded) \n ; all of this gets discarded\nkept'
        tokens = re.finditer(regex, string)
        tags = 'WHITESPACE COMMENT_SEXP WHITESPACE COMMENT SYMBOL'.split()

        for match, expected_tag in zip(tokens, tags):
            self.assertEqual(match.lastgroup, expected_tag)
        actual_tkns = self.lexer.lex(string)
        token = next(actual_tkns)
        self.assertEqual(token, Token('SYMBOL', 'kept', 1, 45))
        # Confirm that that was the only token
        with self.assertRaises(StopIteration):
            token = next(actual_tkns)

    # TODO: add tests to validate symbol names etc


class ParserTest(TestCase):
    lexer = Lexer()
    parser = Parser()

    def test_parse_simple(self):
        '''A simple sexp gets parsed correctly'''
        string = '(print "foo" 1 3.14)'
        tokens = self.lexer.lex(string)
        parsed = next(self.parser.parse(tokens))
        self.assertEquals(parsed, [Symbol('print'), 'foo', 1, 3.14])

    def test_parse_nested(self):
        '''A nested sexp gets parsed correctly'''
        string = '(print (+ "spam" " and eggs"))'
        tokens = self.lexer.lex(string)
        parsed = next(self.parser.parse(tokens))
        self.assertEquals(parsed, ['print', ['+', 'spam', ' and eggs']])


class AtomTest(TestCase):
    def test_make_atom(self):
        '''Tokens get parsed to the correct internal types'''
        token1 = make_atom(Token('SYMBOL', 'print', 0, 0))
        token2 = make_atom(Token('STRING', 'foo', 0, 0))
        token3 = make_atom(Token('NUM_INT', 1, 0, 0))
        token4 = make_atom(Token('NUM_FLOAT', 3.14, 0, 0))
        self.assertEqual(type(token1), Symbol)
        self.assertEqual(type(token2), str)
        self.assertEqual(type(token3), int)
        self.assertEqual(type(token4), float)
