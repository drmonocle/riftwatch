"""Windowless launcher for RiftWatch: pyw run_riftwatch.pyw"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from riftscout.ui.app import run

if __name__ == "__main__":
    run()
