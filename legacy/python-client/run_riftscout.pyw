"""Windowless launcher: double-click, or `pythonw run_riftscout.pyw`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from riftscout.ui.app import run  # noqa: E402

run()
