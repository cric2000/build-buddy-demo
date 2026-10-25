"""Observe test execution and publish Chopper SVG snapshots through BuildBuddy."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
API = "https://build-buddy-kappa.vercel.app/v1/mascot.svg"
STATES = ("queued", "running", "passing", "failing", "unknown")


def result_status(report_path, returncode):
    """A missing, malformed, or inconsistent test report is not a passing result."""
    try:
        report = json.loads(Path(report_path).read_text())
        if not isinstance(report, dict):
            return "unknown", None
        count, failures, code = (report[key] for key in ("tests_run", "failed_tests", "exit_code"))
        if any(type(value) is not int for value in (count, failures, code)):
            return "unknown", None
        if count <= 0 or not 0 <= failures <= count or code not in (0, 1) or code != returncode:
            return "unknown", None
        if (code == 0) != (failures == 0):
            return "unknown", None
        return ("passing" if code == 0 else "failing"), report
    except (OSError, ValueError, KeyError, TypeError):
        return "unknown", None


class TestRun:
    def __init__(self, directory, broken=False):
        self.directory = Path(directory)
        self.report_path = self.directory / "report.json"
        self.gate = self.directory / "start.gate"
        self.process = None
        self.broken = broken

    def status(self):
        if self.process is None:
            return "queued", None
        code = self.process.poll()
        if code is None:
            return "running", None
        return result_status(self.report_path, code)

    def start(self):
        env = os.environ.copy()
        env.pop("PARCEL_DEMO_BUG", None)
        env["PARCEL_DEMO_START_GATE"] = str(self.gate)
        if self.broken:
            env["PARCEL_DEMO_BUG"] = "1"
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/run_tests.py"), "--report", str(self.report_path)],
            cwd=ROOT, env=env,
        )
        deadline = time.monotonic() + 10
        while not self.gate.with_suffix(".ready").exists():
            if self.process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("test worker failed to start")
            time.sleep(0.05)

    def finish(self):
        self.gate.write_text("run tests\n")
        return self.process.wait(timeout=30)

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def render(status, report, output, renderer=None):
    params = {"character": "chopper", "status": status, "theme": "dark", "animate": "false"}
    if status == "failing" and report and report["failed_tests"]:
        params["failed_tests"] = str(report["failed_tests"])
    if renderer:
        command = [renderer, "render", "--output", str(output)]
        for key, value in params.items():
            command.append(f"--{key}={value}")
        subprocess.run(command, check=True)
    else:
        url = API + "?" + urllib.parse.urlencode(params)
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "BuildBuddy-Demo/1.0"})
                with urllib.request.urlopen(request, timeout=20) as response:
                    if response.headers.get_content_type() != "image/svg+xml":
                        raise ValueError("BuildBuddy did not return an SVG")
                    svg = response.read(1_000_001)
                if len(svg) > 1_000_000:
                    raise ValueError("unexpectedly large SVG")
                output.write_bytes(svg)
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
    root = ET.parse(output).getroot()
    title = root.find("{http://www.w3.org/2000/svg}title")
    if root.tag != "{http://www.w3.org/2000/svg}svg" or root.get("data-character") != "chopper":
        raise ValueError("expected a Chopper SVG")
    if title is None or f"{status} build" not in (title.text or ""):
        raise ValueError("SVG status did not match the observed test state")


def run_demo(scenario, output, renderer=None):
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    actual_result = None

    def capture(status, report=None):
        render(status, report, output / f"{status}.svg", renderer)
        results[status] = {"status": status, "test_report": report}
        print(f"Published snapshot: {status}", flush=True)

    with tempfile.TemporaryDirectory(prefix="chopper-tests-") as temporary:
        directory = Path(temporary)
        if scenario in ("all", "unknown"):
            status, report = result_status(directory / "missing-report.json", 0)
            capture(status, report)
        if scenario in ("all", "queued", "running", "passing", "failing"):
            normal = directory / "normal"
            normal.mkdir()
            run = TestRun(normal, broken=scenario == "failing")
            try:
                status, report = run.status()
                capture(status, report)
                if scenario != "queued":
                    run.start()
                    status, report = run.status()
                    capture(status, report)
                    run.finish()
                    status, report = run.status()
                    if status not in ("passing", "failing"):
                        raise RuntimeError("test worker finished without a usable result")
                    capture(status, report)
                    actual_result = status
            finally:
                run.close()
        if scenario == "all":
            broken = directory / "intentional-failure"
            broken.mkdir()
            run = TestRun(broken, broken=True)
            try:
                run.start()
                run.finish()
                status, report = run.status()
                if status != "failing" or not report or report["failed_tests"] == 0:
                    raise RuntimeError("the intentional regression was not caught by tests")
                capture(status, report)
            finally:
                run.close()

    selected = actual_result if scenario in ("all", "passing", "failing") else scenario
    if selected not in results:
        raise RuntimeError(f"did not observe the selected state: {selected}")
    (output / "mascot.svg").write_bytes((output / f"{selected}.svg").read_bytes())
    summary = {"scenario": scenario, "selected_status": selected, "snapshots": results}
    (output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a") as stream:
            stream.write(f"### Chopper demo: {scenario}\n\nSelected snapshot: **{selected}**.\n\n")
            stream.write("| Observed state | Tests run | Failed |\n| --- | ---: | ---: |\n")
            for state, item in results.items():
                report = item["test_report"] or {}
                stream.write(f"| {state} | {report.get('tests_run', '—')} | {report.get('failed_tests', '—')} |\n")
            stream.write("\nQueued/running are lifecycle snapshots; unknown means no usable result. "
                         "The all scenario includes an intentionally failing regression demonstration.\n")
    return 1 if actual_result == "failing" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all",) + STATES, default="all")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "site")
    parser.add_argument("--renderer", help="optional local BuildBuddy CLI instead of the public API")
    args = parser.parse_args()
    return run_demo(args.scenario, args.output_dir, args.renderer)


if __name__ == "__main__":
    sys.exit(main())
