"""
RiftScout entry point.
    py -3.12 -m riftscout          launch the desktop app
    py -3.12 -m riftscout --diag   check every data source from the console
"""

import sys


def main() -> int:
    if "--diag" in sys.argv[1:]:
        from .diag import main as diag_main
        return diag_main()
    from .ui.app import run
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
