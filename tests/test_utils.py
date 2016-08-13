from unittest import TestCase
from ripl.bases import Symbol
from ripl.utils import _ripl_add


class UtilsTest(TestCase):
    # NOTE: all procedures will be given *args at the moment
    def test_add_floats(self):
        args = [2, 1.14, 0.00159]
        self.assertEqual(3.14159, _ripl_add(*args))

    def test_add_ints(self):
        args = [2, 1, 17]
        self.assertEqual(20, _ripl_add(*args))

    def test_add_mixed(self):
        args = [2, 1, 17]
        args += [2.0, 1.14, 0.00159]
        self.assertEqual(23.14159, _ripl_add(*args))

    def test_add_strings(self):
        args = ["this", " and ", "that"]
        self.assertEqual("this and that", _ripl_add(*args))

    def test_add_int_str(self):
        '''You can't add strings and numerics'''
        args = ["string", 5]
        with self.assertRaises(TypeError):
            _ripl_add(*args)
