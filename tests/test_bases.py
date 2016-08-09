from unittest import TestCase
from ripl.bases import Env


class EnvTest(TestCase):
    env = Env()

    def test_find_succeed(self):
        '''We return the env if the var is in it'''
        self.env.update({"foo": "bar"})
        returned_env = self.env.find("foo")
        self.assertEqual(returned_env, self.env)

    def test_find_fail(self):
        '''We get a NameError if we try to access an undefined variable'''
        with self.assertRaises(AttributeError):
            returned_env = self.env.find("foo")
            self.assertEqual(returned_env, self.env)
