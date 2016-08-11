from unittest import TestCase
from ripl.prelude import reverse


class PreludeTest(TestCase):
    # NOTE: all procedures will be given *args at the moment
    def test_reverse(self):
        self.assertEqual('fish', reverse('hsif'))
        self.assertEqual('racecar', reverse('racecar'))
