from unittest import TestCase
from ripl.executors import RiplExecutor


class ExecutorTest(TestCase):
    executor = RiplExecutor()

    def test_py_to_lisp_str(self):
        '''We can print sexps as sexps'''
        s = self.executor.py_to_lisp_str(['print', 'this'])
        self.assertEqual(s, "(print this)")

    def test_py_to_lisp_str_nested(self):
        '''We can print nested sexps as sexps'''
        l = ['print', ['+', '3', '4']]
        s = self.executor.py_to_lisp_str(l)
        self.assertEqual(s, "(print (+ 3 4))")
