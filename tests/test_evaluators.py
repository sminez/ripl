from unittest import TestCase

from ripl.bases import RList
from ripl.evaluators import RiplEvaluator


class ExecutorTest(TestCase):
    executor = RiplEvaluator()

    def test_py_to_lisp_str(self):
        '''We can print sexps as sexps'''
        s = self.executor.py_to_lisp_str(RList(['print', 'this']))
        self.assertEqual(s, "(print this)")

    def test_py_to_lisp_str_nested(self):
        '''We can print nested sexps as sexps'''
        l = RList(['print', RList(['+', '3', '4'])])
        s = self.executor.py_to_lisp_str(l)
        self.assertEqual(s, "(print (+ 3 4))")
