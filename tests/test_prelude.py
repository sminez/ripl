from unittest import TestCase

import ripl.prelude as pr


class PreludeTest(TestCase):
    def test_reverse(self):
        self.assertEqual('fish', pr.reverse('hsif'))
        self.assertEqual('racecar', pr.reverse('racecar'))

    def test_product(self):
        self.assertEqual(pr.product([1, 2, 3, 4, 5]), 120)
        self.assertEqual(pr.product([2, ' a']), ' a a')

    def test_foldl(self):
        pass

    def test_foldr(self):
        pass

    def test_scanl(self):
        pass

    def test_scanr(self):
        pass

    def test_take(self):
        pass

    def test_drop(self):
        pass

    def test_takeWhile(self):
        pass

    def test_dropWhile(self):
        pass

    def test_flatten(self):
        pass

    def test_drain(self):
        pass
