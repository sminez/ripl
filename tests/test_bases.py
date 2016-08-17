from unittest import TestCase

from ripl.evaluators import RiplEvaluator
from ripl.bases import Scope, Keyword, Symbol
from ripl.bases import RList, RVector, RDict, RString, EmptyList


class ScopeTest(TestCase):
    '''This is just sanity checking my use of ChainMap'''
    scope = Scope()

    def test_find_succeed(self):
        '''We return the env if the var is in it'''
        self.scope.update({"foo": "bar"})
        returned = self.scope["foo"]
        self.assertEqual(returned, "bar")

    def test_find_fail(self):
        '''We get None if we try to access an undefined variable'''
        with self.assertRaises(KeyError):
            self.scope["foo"]


class TypeTest(TestCase):
    '''Check that the internal types behave correctly'''
    def test_symbol(self):
        '''Keywords have the expected behaviour'''
        foo = Symbol('foo')
        self.assertNotEqual(foo, 'foo')
        self.assertEqual(foo, Symbol('foo'))
        self.assertNotEqual(foo, Keyword('foo'))
        with self.assertRaises(AttributeError):
            foo._cons(foo)

    def test_keyword(self):
        '''Keywords have the expected behaviour'''
        foo = Keyword('foo')
        self.assertNotEqual(foo, ':foo')
        self.assertEqual(foo, Keyword('foo'))
        self.assertNotEqual(foo, Symbol('foo'))
        with self.assertRaises(AttributeError):
            foo._cons(foo)
        self.assertTrue(foo._keyword_comp(Keyword('foo')))
        self.assertTrue(foo._keyword_comp(Symbol('foo')))
        self.assertTrue(foo._keyword_comp('foo'))

    def test_RList(self):
        '''Ripl's list cons works'''
        self.assertEqual(
                RList([1, 2, 3])._cons(0),
                RList([0, 1, 2, 3]))
        new_list = RList([])._cons(0)
        self.assertFalse(isinstance(new_list, EmptyList))

    def test_RVector(self):
        '''Ripl's vector works'''
        self.assertEqual(
                RVector([1, 2, 3])._cons(0),
                RVector([0, 1, 2, 3]))

    def test_RDict(self):
        '''Ripl's dict works'''
        self.assertEqual(
                RDict({1: 2, 3: 4})._cons([5, 6]),
                RDict({1: 2, 3: 4, 5: 6}))

    def test_RString(self):
        '''Ripl's string works'''
        self.assertEqual(
                RString("<- this got cons-ed!")._cons("foo "),
                RString("foo <- this got cons-ed!"))


class BuiltInTest(TestCase):
    '''Builtin keywords work'''

    def _eval(self, string):
        '''Helper for evals'''
        evaluator = RiplEvaluator()
        tokens = evaluator.reader.lex(string)
        exp = next(evaluator.reader.parse(tokens))
        result = evaluator.eval(exp, evaluator.global_scope)
        return result

    def test_if(self):
        '''if statements evaluate correctly'''
        string = '(if (== 3 (+ 1 2)) 1 0)'
        result = self._eval(string)
        self.assertEqual(result, 1)
