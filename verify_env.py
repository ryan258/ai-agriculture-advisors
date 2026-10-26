"""Compatibility entry point for private offline diagnostics."""

import sys
from lib.operations import doctor

if __name__ == "__main__":
    raise SystemExit(doctor(live="--live" in sys.argv[1:]))
