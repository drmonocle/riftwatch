"""Windowless launcher for RiftWatch: pyw run_riftwatch.pyw"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from riftscout.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
