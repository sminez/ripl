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
        '''Argparse isn't borked'''
        argv = '--version'
        with suppress(SystemExit), Capturing() as output:
            cli.main(argv)

        output = '\n'.join(l for l in output)
        self.assertEqual(output, cli.__version__)

    def test_parse_cmdln_sexp(self):
        '''The CLI can parse an s-expression'''
        argv = '-s (print (+ "Yay! This" " all works!"))'
        with suppress(SystemExit), Capturing() as output:
            cli.main(argv)

        output = '\n'.join(l for l in output)
        self.assertEqual(output, "Yay! This all works!")
