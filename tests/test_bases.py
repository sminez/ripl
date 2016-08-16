from unittest import TestCase
from ripl.bases import Scope


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
