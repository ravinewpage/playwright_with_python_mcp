#!/usr/bin/env python3
"""Test runner with scenario-based execution and parallel processing.

Usage:
  python run_tests.py --scenario e2e                    # Run E2E tests
  python run_tests.py --scenario kids                   # Run Kids clothing tests
  python run_tests.py --scenario all --parallel         # Run all in parallel
  python run_tests.py --scenario smoke --parallel -n 4  # 4 workers
"""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path


SCENARIOS = {
    "e2e": {
        "pattern": "kohls_end_to_end",
        "description": "End-to-end shopping flow (login → search → product → cart → checkout)",
    },
    "kids": {
        "pattern": "kids_clothing",
        "description": "Kids clothing category browse (no login needed, avoids bot-blocking)",
    },
    "smoke": {
        "pattern": "smoke",
        "description": "All smoke tests (both E2E and Kids)",
    },
    "all": {
        "pattern": None,
        "description": "All tests",
    },
}


def run_tests(
    scenario: str,
    parallel: bool = False,
    workers: int | None = None,
    verbose: bool = True,
    headless: bool = False,
) -> int:
    """Run tests for a specific scenario.

    Args:
        scenario: One of 'e2e', 'kids', 'smoke', 'all'
        parallel: Enable parallel execution with pytest-xdist
        workers: Number of parallel workers (auto if None)
        verbose: Enable verbose output
        headless: Run browser in headless mode

    Returns:
        Exit code from pytest
    """
    if scenario not in SCENARIOS:
        print(f"❌ Unknown scenario: {scenario}")
        print(f"Available: {', '.join(SCENARIOS.keys())}")
        return 1

    scenario_info = SCENARIOS[scenario]
    print(f"\n🎯 Running {scenario.upper()} tests")
    print(f"   Description: {scenario_info['description']}")
    print()

    # Build pytest command
    cmd = ["pytest", "tests/"]

    # Add test selection
    if scenario == "smoke":
        cmd.append("-m")
        cmd.append("smoke")
    elif scenario != "all":
        cmd.append("-k")
        cmd.append(scenario_info["pattern"])

    # Add verbosity
    if verbose:
        cmd.append("-v")

    cmd.append("-s")  # Show output

    # Add parallel support
    if parallel:
        cmd.append("-n")
        cmd.append(str(workers) if workers else "auto")
        print(f"⚡ Parallel execution enabled")
        if workers:
            print(f"   Workers: {workers}")
        else:
            print(f"   Workers: auto (CPU count)")
    else:
        print(f"🔄 Sequential execution")

    print(f"   Command: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Kohls.com automation tests by scenario",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --scenario e2e
  python run_tests.py --scenario kids --parallel
  python run_tests.py --scenario smoke --parallel -n 4
  python run_tests.py --scenario all --parallel
        """,
    )

    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="smoke",
        help="Test scenario to run (default: smoke)",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel execution with pytest-xdist",
    )

    parser.add_argument(
        "-n",
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: auto/CPU count)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_false",
        dest="verbose",
        help="Reduce output verbosity",
    )

    args = parser.parse_args()

    # Print available scenarios
    print("📋 Available scenarios:")
    for name, info in SCENARIOS.items():
        print(f"   • {name:8} - {info['description']}")
    print()

    # Run tests
    exit_code = run_tests(
        scenario=args.scenario,
        parallel=args.parallel,
        workers=args.workers,
        verbose=args.verbose,
    )

    # Print summary
    print()
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
