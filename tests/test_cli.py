import sys
import unittest

from io import StringIO
from contextlib import suppress

import ripl.cli as cli


# Solution for capturing stdout from http://goo.gl/oKF2jV
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


class CLITest(unittest.TestCase):
    def test_cli(self):
        argv = '--version'
        with suppress(SystemExit), Capturing() as output:
            cli.main(argv)

        output = '\n'.join(l for l in output)
        self.assertEqual(output, cli.__version__)
