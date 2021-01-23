"""
TODO document
"""
import argparse
import logging
import sys
from time import sleep

from .server import Server

log = logging.getLogger("folderbrowser.main")
log.setLevel(logging.DEBUG)

# create console handler and set level to info
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)


def main(args):
    """
    Runs a folderbrowser.
    Does not return.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--bind-address",
        help="Address to listen on (default = %(default)s)",
        default="127.0.0.1",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to listen on (default = %(default)d)",
        default=8080,
    )
    # pylint: disable=unused-variable
    options = parser.parse_args(args)
    server = Server(log, bind_address=options.bind_address, port=options.port)
    sleep(9999999)


if __name__ == "__main__":
    main(sys.argv[1:])
