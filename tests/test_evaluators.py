from unittest import TestCase

from ripl.bases import RList, Symbol
from ripl.evaluators import RiplEvaluator


class EvaluatorTest(TestCase):
    evaluator = RiplEvaluator()

    def _eval(self, string):
        '''Helper for evals'''
        tokens = self.evaluator.reader.lex(string)
        exp = next(self.evaluator.reader.parse(tokens))
        result = self.evaluator.eval(exp, self.evaluator.global_scope)
        return result

    def test_py_to_lisp_str(self):
        '''We can print sexps as sexps'''
        s = self.evaluator.py_to_lisp_str(RList(['print', 'this']))
        self.assertEqual(s, "(print this)")

    def test_py_to_lisp_str_nested(self):
        '''We can print nested sexps as sexps'''
        l = RList(['print', RList(['+', '3', '4'])])
        s = self.evaluator.py_to_lisp_str(l)
        self.assertEqual(s, "(print (+ 3 4))")

    def test_dict_print(self):
        '''Dicts print correctly'''
        d = {1: 2, 3: 4, 5: 6}
        s = self.evaluator.py_to_lisp_str(d)
        self.assertEqual(s, '{1 2, 3 4, 5 6}')

    def test_vector_print(self):
        '''Vectors print correctly'''
        d = [1, 2, 3, 4, 5]
        s = self.evaluator.py_to_lisp_str(d)
        self.assertEqual(s, '[1 2 3 4 5]')

    def test_simple_sexp(self):
        '''A single function call works'''
        string = '(+ 2 3)'
        result = self._eval(string)
        self.assertEqual(result, 5)

    def test_nested_sexp(self):
        '''Nested function calls are evaluated correctly'''
        string = '(* (+ 2 (% 9 3) 5) (max 7 1 10))'
        result = self._eval(string)
        self.assertEqual(result, 70)

    def test_undeclared_variable(self):
        '''Undeclared variables raise a NameError'''
        with self.assertRaises(NameError):
            self.evaluator.eval(Symbol('foo'), self.evaluator.global_scope)

    def test_empty_list_works(self):
        '''The empty list gets evalled correctly'''
        string = '()'
        result = self._eval(string)
        self.assertEqual(result, None)
        self.assertEqual(result, RList())
