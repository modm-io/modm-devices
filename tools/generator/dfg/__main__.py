# Copyright 2026, Niklas Hauser
# SPDX-License-Identifier: MPL-2.0

import logging
import argparse
from pathlib import Path
from multiprocessing import Pool

from dfg.jobs import expand_targets, generate_job

LOGGER = logging.getLogger("dfg")


def main():
    parser = argparse.ArgumentParser(
        description="Generate modm device files from the modm-data pipelines."
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Device prefixes (comma-separated to merge together), vendors or 'all'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "devices",
        help="Output folder for the device files.",
    )
    parser.add_argument(
        "--jobs", type=int, default=None, help="Number of parallel jobs."
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Do not verify the merged device files.",
    )
    parser.add_argument(
        "--log-level", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level, format="[%(levelname)s] %(name)s: %(message)s"
    )
    success = True
    calls = [
        (job, args.output, not args.no_verify, args.log_level)
        for job in expand_targets(args.targets)
    ]
    with Pool(args.jobs) as pool:
        for job, count, paths, duration, error in pool.starmap(
            generate_job, calls, chunksize=1
        ):
            if error:
                success = False
                LOGGER.error("Generating %s failed:\n%s", ",".join(job), error)
            else:
                print(
                    f"{','.join(job)}: {count} devices -> {len(paths)} files in {duration:.1f}s"
                )
    return success


if __name__ == "__main__":
    exit(0 if main() else 1)
