#!/usr/bin/env python3
"""
run_all_v4.py: Unified entrypoint wrapper pointing to run_v4_pipeline.py.
Eliminates diverging runner logic and enforces unified execution gates (P0-05).
"""

import sys
import os

_script_dir = os.path.abspath(os.path.dirname(__file__))
_repo_root = os.path.abspath(os.path.join(_script_dir, "../.."))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

if __name__ == "__main__":
    from run_v4_pipeline import main
    main()
