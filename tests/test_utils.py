from unittest import TestCase
from ripl.types import RiplSymbol, RiplString, RiplInt, RiplFloat
from ripl.utils import _ripl_add, make_atom


class UtilsTest(TestCase):
    # NOTE: all procedures will be given *args at the moment
    def test_add_floats(self):
        args = [RiplFloat(x) for x in ['2', '1.14', '0.00159']]
        self.assertEqual(3.14159, _ripl_add(*args))

    def test_add_ints(self):
        args = [RiplInt(x) for x in ['2', '1', '17']]
        self.assertEqual(20, _ripl_add(*args))

    def test_add_mixed(self):
        args = [RiplInt(x) for x in ['2', '1', '17']]
        args += [RiplFloat(x) for x in ['2', '1.14', '0.00159']]
        self.assertEqual(23.14159, _ripl_add(*args))

    def test_add_strings(self):
        args = [RiplString(x) for x in ["this", " and ", "that"]]
        self.assertEqual("this and that", _ripl_add(*args))

    def test_add_int_str(self):
        '''You can't add strings and numerics'''
        args = ["string", RiplInt('5')]
        with self.assertRaises(TypeError):
            _ripl_add(*args)

    def test_atom(self):
        '''Tokens get parsed to the correct internal types'''
        token1 = make_atom('print')
        token2 = make_atom('"foo"')
        token3 = make_atom('1')
        token4 = make_atom('3.14')
        self.assertEqual(type(token1), RiplSymbol)
        self.assertEqual(type(token2), RiplString)
        self.assertEqual(type(token3), RiplInt)
        self.assertEqual(type(token4), RiplFloat)
