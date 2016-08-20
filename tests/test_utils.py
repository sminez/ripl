from unittest import TestCase

from ripl.bases import Scope, Symbol, get_global_scope
from ripl.utils import _ripl_add, curry, pyimport


class RiplAddTest(TestCase):
    # NOTE: all procedures will be given *args at the moment
    def test_add_floats(self):
        '''Just adding floats works'''
        args = [2, 1.14, 0.00159]
        self.assertEqual(3.14159, _ripl_add(*args))

    def test_add_ints(self):
        '''Just adding ints works'''
        args = [2, 1, 17]
        self.assertEqual(20, _ripl_add(*args))

    def test_add_mixed(self):
        '''Adding mixed numerics works'''
        args = [2, 1, 17]
        args += [2.0, 1.14, 0.00159]
        self.assertEqual(23.14159, _ripl_add(*args))

    def test_add_strings(self):
        '''Strings get joined'''
        args = ["this", " and ", "that"]
        self.assertEqual("this and that", _ripl_add(*args))

    def test_add_int_str(self):
        '''You can't add strings and numerics'''
        args = ["string", 5]
        with self.assertRaises(TypeError):
            _ripl_add(*args)


class PyimportTest(TestCase):
    def test_import_bare_scope(self):
        '''Importing to an empty Scope works'''
        updated_scope = pyimport('math', Scope())
        self.assertTrue(Symbol('math.sin') in updated_scope)

    def test_import_std_scope(self):
        '''Importing to the standard Scope works and doesn't clobber'''
        updated_scope = pyimport('math', get_global_scope())
        self.assertTrue(Symbol('math.sin') in updated_scope)
        self.assertTrue(Symbol('car') in updated_scope)

    def test_import_as(self):
        '''Importing foo as f works'''
        updated_scope = pyimport('math', Scope(), _as='foo')
        self.assertTrue(Symbol('foo.sin') in updated_scope)
        self.assertFalse(Symbol('math.sin') in updated_scope)

    def test_import_from(self):
        '''From foo import bar works'''
        updated_scope = pyimport('math', get_global_scope(), _from='sin')
        self.assertTrue(Symbol('sin') in updated_scope)
        self.assertFalse(Symbol('math.sin') in updated_scope)

    def test_import_bad_module(self):
        '''Trying to import a non-existant module fails correctly'''
        with self.assertRaises(ImportError):
            pyimport('notamodule', Scope())

    def test_import_from_as(self):
        '''Trying to import from and as fails correctly'''
        with self.assertRaises(SyntaxError):
            pyimport('math', Scope(), _as='foo', _from='sin')


class CurryTest(TestCase):
    def test_simple_positional(self):
        '''
        A func with two positional args, given one positional arg
        returns a func that takes one positional arg.
        '''
        def func(a, b):
            return '1st: {}, 2nd: {}'.format(a, b)
        curried = curry(func, 'first')
        self.assertEqual(curried('second'), '1st: first, 2nd: second')

    def test_chained_positional(self):
        '''
        Chaining two calls two curry with positional args works
        '''
        def func2(a, b, c):
            return '{} {} {}!'.format(a, b, c)
        curried = curry(func2, 'this')
        double_curried = curry(curried, 'is')
        self.assertEqual(double_curried('awesome'), 'this is awesome!')

    def test_simple_keyword(self):
        '''
        A func with two keyword args, given one keyword arg
        returns a func that takes one positional arg.
        '''
        def func(a, b):
            return '1st: {}, 2nd: {}'.format(a, b)
        curried = curry(func, {'a': 'first'})
        self.assertEqual(curried(**{'b': 'second'}), '1st: first, 2nd: second')

    def test_chained_keyword(self):
        '''
        Chaining two calls two curry with keyword args works
        '''
        def func2(a, b, c):
            return '{} {} {}?'.format(a, b, c)
        curried = curry(func2, {'b': 'this'})
        double_curried = curry(curried, {'a': 'is'})
        self.assertEqual(
                double_curried(**{'c': 'awesome'}),
                'is this awesome?')
