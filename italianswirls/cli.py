"""CLI to start the language server"""

import argparse
import logging

from italianswirls.server import LS

DESCRIPTION = "Italian Swirls, a minimal Python language server based on Jedi."
DEFAULT_LOG_FILE = "/tmp/italianswirls.log"


def main():
    argparser = argparse.ArgumentParser(description=DESCRIPTION)
    argparser.add_argument("-d", "--debug", nargs="?", const=DEFAULT_LOG_FILE,
                           help=f"debug log (default: {DEFAULT_LOG_FILE})")
    args = argparser.parse_args()

    if debug_log_file := args.debug:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(logging.FileHandler(debug_log_file))

    LS.start_io()


if __name__ == "__main__":
    main()
