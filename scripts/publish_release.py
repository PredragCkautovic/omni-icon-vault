#!/usr/bin/env python3
"""Preflight and publish an Omni Icon Vault tag.

The GitHub Actions release workflow performs the actual release build/upload.
This script intentionally does not rewrite an existing version tag.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text("utf-8").strip()
TAG = f"v{VERSION}"


def run(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def output(*args: str) -> str:
    p = run(*args, capture=True)
    return p.stdout.strip()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Preflight and publish the current Omni release tag.")
    ap.add_argument("--dry-run", action="store_true", help="validate only; do not push or create a tag")
    ap.add_argument("--skip-tests", action="store_true", help="skip local unit tests")
    args = ap.parse_args()

    if not shutil.which("git"):
        fail("git was not found in PATH")
    if not shutil.which("gh"):
        fail("GitHub CLI (gh) was not found in PATH")

    print(f"Omni Icon Vault {VERSION} release preflight")
    run("gh", "auth", "status")

    if output("git", "status", "--porcelain"):
        fail("working tree is not clean; commit or stash changes first")

    remotes = output("git", "remote").splitlines()
    if "origin" not in remotes:
        fail("origin remote is missing")

    branch = output("git", "branch", "--show-current")
    if branch != "main":
        fail(f"current branch is {branch!r}; switch to 'main' before releasing")

    if not args.skip_tests:
        run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
        run(sys.executable, "-m", "compileall", "-q", "install.py", "uninstall.py", "omni.py", "tools", "scripts", "tests")

    local_tag = run("git", "rev-parse", "-q", "--verify", f"refs/tags/{TAG}", check=False, capture=True)
    remote_tag = run("git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{TAG}", check=False, capture=True)
    if local_tag.returncode == 0 or remote_tag.returncode == 0:
        fail(f"tag {TAG} already exists; bump VERSION instead of moving a published version tag")

    print(f"Ready to publish {TAG} from main.")
    if args.dry_run:
        print("Dry run complete; nothing was pushed.")
        return 0

    run("git", "push", "origin", "main")
    run("git", "tag", "-a", TAG, "-m", f"Omni Icon Vault {VERSION}")
    run("git", "push", "origin", TAG)

    print(f"\nTag {TAG} pushed. GitHub Actions will build and publish the release.")
    print("Watch it with: gh run watch")
    print(f"Open it with: gh release view {TAG} --web")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
