# BuildBuddy demo · Chopper's parcel tests

A tiny Python shipping calculator with **12 real tests** and a GitHub Actions workflow that turns their lifecycle and results into Chopper artwork using [BuildBuddy](https://github.com/cric2000/build-buddy).

**[Run a demo →](https://github.com/cric2000/build-buddy-demo/actions/workflows/chopper.yml)** · **[Read the workflow](.github/workflows/chopper.yml)** · **[Latest published results](https://github.com/cric2000/build-buddy-demo/blob/badge-artifact/results.json)**

## Latest selected snapshot

<!-- buildbuddy:latest:start -->
**Passing · 12 tests · 0 failures**

![Latest selected Chopper test snapshot](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/mascot.svg)

[View this run](https://github.com/cric2000/build-buddy-demo/actions/runs/40239665227) · [Tested source](https://github.com/cric2000/build-buddy-demo/commit/df3b068fe0a50190f19dc1f1101c5aa2e26042fd) · [Published results](https://github.com/cric2000/build-buddy-demo/blob/76005dc6a68222f14b0c72d60b78293d246df9cf/results.json)
<!-- buildbuddy:latest:end -->

This image records the selected scenario at the moment it was observed. It is not a continuously polled indicator of whether a GitHub runner is currently busy. Actions publishes images to `badge-artifact` and updates the generated README blocks with immutable image URLs, the observed status, and a link to the test run. A new image URL for each publication prevents GitHub from reusing an older cached result.

## All five states · demonstration gallery

These examples intentionally include a failing run with two failed tests. The latest selected result is shown above.

<!-- buildbuddy:gallery:start -->
| Queued | Running | Passing | Failing | Unknown |
| --- | --- | --- | --- | --- |
| ![Queued Chopper](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/queued.svg) | ![Running Chopper](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/running.svg) | ![Passing Chopper](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/passing.svg) | ![Failing Chopper](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/failing.svg) | ![Unknown Chopper](https://raw.githubusercontent.com/cric2000/build-buddy-demo/76005dc6a68222f14b0c72d60b78293d246df9cf/unknown.svg) |
<!-- buildbuddy:gallery:end -->

| Scenario | What actually happens |
| --- | --- |
| `queued` | A test task exists but its subprocess has not started. |
| `running` | A real test worker starts and waits at a coordination gate. Its process is confirmed alive before the snapshot; it then runs and finishes normally. |
| `passing` | All 12 shipping assertions pass. The report agrees with the worker's zero exit code. |
| `failing` | An explicitly enabled demo regression moves the free-shipping threshold by one cent. Two real boundary tests fail, and the workflow ends red after publishing Chopper. |
| `unknown` | No test report exists. The resolver cannot determine an outcome and shows curious Chopper. Malformed or inconsistent reports also resolve to unknown. |
| `all` | Records all five states, verifies the intentional regression is caught, and selects the normal test run's result for the main image. The expected negative demonstration does not make a successful full demo red. |

Queued, running, and unknown are lifecycle/availability states, not additional pass/fail verdicts. The failure count comes from Python's test runner; it is not a number hard-coded into an image URL. These images are rendered with animation disabled so their expressions remain readable in GitHub.

## Try it on GitHub

1. Open **Actions → Chopper test demo → Run workflow** on `main` (requires permission to run workflows in this repository).
2. Select `queued`, `running`, `passing`, `failing`, `unknown`, or `all`.
3. Open the run to inspect actual assertions, the observed-state summary, and downloadable SVG/report artifacts.
4. Return here after publication. The generated status text and image URL update together after publication. Reload the page to see the new README commit.

Visitors can inspect every run and fork the repository to run their own scenarios. A push to `main` automatically runs `all`. Pull requests verify the application and lifecycle tests but cannot publish images. Manual runs from other branches also cannot publish. Only the separate publication job receives repository write permission. Concurrent runs are serialized to avoid racing image updates. `badge-artifact` is reserved for generated images and results; source code remains on `main`. The publication job also commits only the generated README blocks on `main`; its repository token and `[skip ci]` commit message prevent recursive workflow runs.

The published gallery keeps each state's latest snapshot. A single-state run updates the selected image and any states it observes; `all` refreshes all five. Infrastructure/API failures are reported as workflow errors and leave the last successfully published image in place, rather than labelling an unobserved result as passing.

## Run locally

Python 3.10 or later; no third-party packages, API key, or deployment needed.

```bash
python3 -m unittest discover -v
python3 scripts/demo.py --scenario all
python3 scripts/demo.py --scenario failing  # exits 1 after rendering actual failures
python3 scripts/demo.py --scenario unknown
```

The verification suite contains 12 shipping tests, 5 integration/report tests, and 3 README publication tests. Its intentional-regression check runs a child test process that is expected to fail; the parent assertion verifies the two failures and passes.

Artwork and `results.json` are written to the ignored `site/` directory. By default, the demo requests SVGs from `https://build-buddy-kappa.vercel.app/v1/mascot.svg`, with status derived from observed process/report state. It uploads no source code, logs, or personal data to BuildBuddy.

If you already have the BuildBuddy CLI, use the identical renderer offline:

```bash
python3 scripts/demo.py --scenario all --renderer /absolute/path/to/buildbuddy
```

## What is being tested?

`parcel.py` calculates shipping in integer cents: $5 for the first kilogram, $1 per additional started kilogram, free standard shipping from $50, and a $12.50 express surcharge. Tests cover weight boundaries, the free-shipping boundary, express pricing, and invalid inputs.

`PARCEL_DEMO_BUG=1` deliberately changes the threshold to $50.01 inside the demo worker only. Normal application behavior and verification runs do not enable it.

Use this repository as a reference for feeding your own test runner's exit code and report into BuildBuddy. Replace the parcel tests with your project's assertions; keep the result validation and separate publication job.

MIT licensed. Built by [Anmol Lamba](https://github.com/cric2000).
