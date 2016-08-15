import argparse

from .executors import RiplRepl


__version__ = "0.1.1"


def main(argv=None):
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     'file_name',
    #     required=False,
    # )
    parser.add_argument(
        '-s',
        '--script',
        type=str,
        default='',
        required=False,
    )
    parser.add_argument(
        '-v',
        '--version',
        action='store_true',
        required=False,
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        required=False,
    )

    if argv:
        args = parser.parse_args([argv])
    else:
        args = parser.parse_args()

    if args.version:
        print(__version__)
    elif args.script:
        repl = RiplRepl()
        repl.eval_and_print(args.script, repl.environment)
    else:
        # Spin up a repl with optional debug
        repl = RiplRepl(debug=args.debug)
        repl.repl()
