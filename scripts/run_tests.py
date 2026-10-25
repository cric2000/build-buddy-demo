"""Run real unittest assertions and write a machine-readable result."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    gate = os.environ.get("PARCEL_DEMO_START_GATE")
    if gate:
        gate = Path(gate)
        gate.with_suffix(".ready").write_text("worker started\n")
        deadline = time.monotonic() + 180
        while not gate.exists():
            if time.monotonic() > deadline:
                raise TimeoutError("demo coordinator did not release the test worker")
            time.sleep(0.05)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_parcel.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    code = 0 if result.wasSuccessful() else 1
    args.report.write_text(json.dumps({
        "tests_run": result.testsRun,
        "failed_tests": len(result.failures) + len(result.errors),
        "exit_code": code,
    }) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
