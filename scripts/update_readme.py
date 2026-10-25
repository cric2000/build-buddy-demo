"""Pin generated README images to one immutable artwork commit."""
import argparse
import json
import os
from pathlib import Path
import re


def update_readme(text, artifact_sha, repository, run_id, source_sha, summary):
    if not all(re.fullmatch(r"[0-9a-f]{40}", sha) for sha in (artifact_sha, source_sha)):
        raise ValueError("expected full Git commit hashes")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid GitHub repository")
    if not re.fullmatch(r"[0-9]+", str(run_id)):
        raise ValueError("invalid workflow run ID")
    states = ("queued", "running", "passing", "failing", "unknown")
    selected = summary["selected_status"]
    if selected not in states:
        raise ValueError("invalid selected state")
    report = summary["snapshots"][selected]["test_report"]
    label = selected.capitalize()
    if report:
        label += f" · {int(report['tests_run'])} tests · {int(report['failed_tests'])} failures"
    base = f"https://raw.githubusercontent.com/{repository}/{artifact_sha}"
    latest = (f"**{label}**\n\n"
              f"![Latest selected Chopper test snapshot]({base}/mascot.svg)\n\n"
              f"[View this run](https://github.com/{repository}/actions/runs/{run_id}) · "
              f"[Tested source](https://github.com/{repository}/commit/{source_sha}) · "
              f"[Published results](https://github.com/{repository}/blob/{artifact_sha}/results.json)")
    gallery = ("| Queued | Running | Passing | Failing | Unknown |\n"
               "| --- | --- | --- | --- | --- |\n| " + " | ".join(
                   f"![{state.capitalize()} Chopper]({base}/{state}.svg)" for state in states
               ) + " |")
    for name, content in (("latest", latest), ("gallery", gallery)):
        start, end = f"<!-- buildbuddy:{name}:start -->", f"<!-- buildbuddy:{name}:end -->"
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError(f"README needs exactly one {name} block")
        before, remainder = text.split(start)
        _, after = remainder.split(end)
        text = before + start + "\n" + content + "\n" + end + after
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-sha", required=True)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()
    summary = json.loads(args.results.read_text())
    args.readme.write_text(update_readme(
        args.readme.read_text(), args.artifact_sha, os.environ["GITHUB_REPOSITORY"],
        os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_SHA"], summary,
    ))


if __name__ == "__main__":
    main()
