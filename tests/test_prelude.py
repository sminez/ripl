import operator as op
from unittest import TestCase

import ripl.prelude as pr
from ripl.bases import RList


class PythonPreludeTest(TestCase):
    '''
    To reduce boiler plate, we are only testing the prelude functions as
    python funtions rather than calls inside of RIPL.
        We have tests that cover import and calling imported functions already
        so if these pass the whole thing should work. (Hopefully!)
    '''
    def test_reverse(self):
        self.assertEqual('fish', pr.reverse('hsif'))
        self.assertEqual('racecar', pr.reverse('racecar'))

    def test_product(self):
        self.assertEqual(pr.product([1, 2, 3, 4, 5]), 120)
        self.assertEqual(pr.product([2, ' a']), ' a a')
        self.assertEqual(pr.product(range(1, 11)), 3628800)

    def test_foldl(self):
        self.assertEqual(pr.foldl(op.sub, 0, [1, 2, 3]), -6)
        self.assertEqual(pr.foldl(op.sub, 0, (n for n in [1, 2, 3])), -6)
        self.assertEqual(pr.foldl(op.add, '', [c for c in 'word']), 'word')

    def test_foldr(self):
        self.assertEqual(pr.foldr(op.sub, 0, [1, 2, 3]), 2)
        self.assertEqual(pr.foldr(op.sub, 0, (n for n in [1, 2, 3])), 2)
        self.assertEqual(pr.foldr(op.add, '', [c for c in 'word']), 'word')

    def test_scanl(self):
        self.assertEqual(
                pr.scanl(op.sub, 0, [1, 2, 3]),
                [0, -1, -3, -6])
        self.assertEqual(
                pr.scanl(op.sub, 0, (n for n in [1, 2, 3])),
                [0, -1, -3, -6])
        self.assertEqual(
                pr.scanl(op.add, '', [c for c in 'word']),
                ['', 'w', 'wo', 'wor', 'word'])

    def test_scanr(self):
        self.assertEqual(
                pr.scanr(op.sub, 0, [1, 2, 3]),
                [0, 3, -1, 2])
        self.assertEqual(
                pr.scanr(op.sub, 0, (n for n in [1, 2, 3])),
                [0, 3, -1, 2])
        self.assertEqual(
                pr.scanr(op.add, '', [c for c in 'word']),
                ['', 'd', 'rd', 'ord', 'word'])

    def test_take(self):
        self.assertEqual(pr.take(3, [1, 2, 3, 4, 5, 6]), [1, 2, 3])
        self.assertEqual(pr.take(3, [1, 2]), [1, 2])
        self.assertEqual(
                pr.take(3, (n for n in[1, 2, 3, 4, 5, 6])),
                [1, 2, 3])
        self.assertEqual(
                pr.take(3, (n for n in [1, 2])),
                [1, 2])
        self.assertEqual(pr.take(3, []), [])

    def test_drop(self):
        self.assertEqual(pr.take(3, [1, 2, 3, 4, 5, 6]), [1, 2, 3])
        self.assertEqual(pr.take(3, [1, 2]), [1, 2])
        self.assertEqual(
                pr.take(3, (n for n in[1, 2, 3, 4, 5, 6])),
                [1, 2, 3])
        self.assertEqual(
                pr.take(3, (n for n in [1, 2])),
                [1, 2])
        self.assertEqual(pr.take(3, []), [])

    def test_takeWhile(self):
        self.assertEqual(pr.take(3, [1, 2, 3, 4, 5, 6]), [1, 2, 3])
        self.assertEqual(pr.take(3, [1, 2]), [1, 2])
        self.assertEqual(
                pr.take(3, (n for n in[1, 2, 3, 4, 5, 6])),
                [1, 2, 3])
        self.assertEqual(
                pr.take(3, (n for n in [1, 2])),
                [1, 2])
        self.assertEqual(pr.take(3, []), [])

    def test_dropWhile(self):
        self.assertEqual(pr.take(3, [1, 2, 3, 4, 5, 6]), [1, 2, 3])
        self.assertEqual(pr.take(3, [1, 2]), [1, 2])
        self.assertEqual(
                pr.take(3, (n for n in[1, 2, 3, 4, 5, 6])),
                [1, 2, 3])
        self.assertEqual(
                pr.take(3, (n for n in [1, 2])),
                [1, 2])
        self.assertEqual(pr.take(3, []), [])

    def test_flatten(self):
        self.assertEqual(
                pr.flatten([[0], 1, [[2, 3], 4, [5, 6, [7]]], [8]]),
                [0, 1, 2, 3, 4, 5, 6, 7, 8])

    def test_drain(self):
        self.assertEqual(
                pr.drain((n for n in [1, 2, 3, 4])),
                RList([1, 2, 3, 4]))
