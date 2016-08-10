from unittest import TestCase
from ripl.executors import RiplExecutor, RiplList, Procedure


class ExecutorTest(TestCase):
    executor = RiplExecutor()

    def test_py_to_lisp_str(self):
        '''We can print sexps as sexps'''
        s = self.executor.py_to_lisp_str(RiplList(['print', 'this']))
        self.assertEqual(s, "(print this)")

    def test_py_to_lisp_str_nested(self):
        '''We can print nested sexps as sexps'''
        l = RiplList(['print', RiplList(['+', '3', '4'])])
        s = self.executor.py_to_lisp_str(l)
        self.assertEqual(s, "(print (+ 3 4))")


class ProcedureTest(TestCase):
    proc = Procedure(None, None, None)
