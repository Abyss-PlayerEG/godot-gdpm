#!/usr/bin/env python3
"""Deploy the self-hosted Godot download CDN worker (Cloudflare).

Usage:
    python3 scripts/deploy_worker.py             # deploy live
    python3 scripts/deploy_worker.py --dry-run   # bundle check only, no upload
    python3 scripts/deploy_worker.py --whoami    # show wrangler auth status

Requires: Node.js (npx) and a one-time `npx wrangler login`
(run inside src/gdpm_cf_workers/).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
WORKER_DIR = PROJECT_DIR / "src" / "gdpm_cf_workers"


def run(args: list[str]) -> int:
    """Run a command with inherited stdio inside WORKER_DIR, return exit code."""
    return subprocess.run(args, cwd=WORKER_DIR, check=False).returncode


def main() -> int:
    """Preflight auth, then deploy (or dry-run/whoami passthrough)."""
    parser = argparse.ArgumentParser(
        description="Deploy the godot-download Cloudflare Worker."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="bundle and validate locally without uploading",
    )
    parser.add_argument(
        "--whoami",
        action="store_true",
        help="show wrangler auth status and exit",
    )
    opts = parser.parse_args()

    if not (WORKER_DIR / "wrangler.toml").is_file():
        print(f"Error: wrangler.toml not found under {WORKER_DIR}", file=sys.stderr)
        return 1
    if shutil.which("npx") is None:
        print("Error: npx not found. Install Node.js first.", file=sys.stderr)
        return 1

    if opts.whoami:
        return run(["npx", "wrangler", "whoami"])

    if opts.dry_run:
        print("Bundling worker (dry-run, no upload)...", flush=True)
        return run(["npx", "wrangler", "deploy", "--dry-run"])

    # Auth preflight: fail early with a hint instead of mid-deploy
    if run(["npx", "wrangler", "whoami"]) != 0:
        print(
            "\nNot logged in. Run once:\n"
            "  cd src/gdpm_cf_workers && npx wrangler login",
            file=sys.stderr,
        )
        return 1

    print("Deploying godot-download worker (live)...", flush=True)
    code = run(["npx", "wrangler", "deploy"])
    if code == 0:
        print("\nDone. Endpoint: https://godot-download.playereg.top")
    return code


if __name__ == "__main__":
    sys.exit(main())
