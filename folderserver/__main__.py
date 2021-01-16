"""
TODO document
"""
import logging
from time import sleep

from .legacy import Server

log = logging.getLogger("folderserver.main")
log.setLevel(logging.DEBUG)

# create console handler and set level to info
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)


def main():
    """
    Runs a folderserver.
    Does not return.
    """
    # pylint: disable=unused-variable
    server = Server(log)
    sleep(9999999)


if __name__ == "__main__":
    main()
