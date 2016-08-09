from unittest import TestCase
from ripl.types import RiplFloat, RiplInt, RiplString
from ripl.prelude import ripl_add, reverse


class PreludeTest(TestCase):
    # NOTE: all procedures will be given *args at the moment
    def test_add_floats(self):
        args = [RiplFloat(x) for x in ['2', '1.14', '0.00159']]
        self.assertEqual(3.14159, ripl_add(*args))

    def test_add_ints(self):
        args = [RiplInt(x) for x in ['2', '1', '17']]
        self.assertEqual(20, ripl_add(*args))

    def test_add_mixed(self):
        args = [RiplInt(x) for x in ['2', '1', '17']]
        args += [RiplFloat(x) for x in ['2', '1.14', '0.00159']]
        self.assertEqual(23.14159, ripl_add(*args))

    def test_add_strings(self):
        args = [RiplString(x) for x in ["this", " and ", "that"]]
        self.assertEqual("this and that", ripl_add(*args))

    def test_add_int_str(self):
        '''You can't add strings and numerics'''
        args = ["string", RiplInt('5')]
        with self.assertRaises(TypeError):
            ripl_add(*args)

    def test_reverse(self):
        self.assertEqual('fish', reverse('hsif'))
        self.assertEqual('racecar', reverse('racecar'))
