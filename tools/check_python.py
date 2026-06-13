from __future__ import annotations

import argparse
import sys


MIN_VERSION = (3, 11)


def parse_version(value: str) -> tuple[int, int]:
    major, _, minor = value.partition(".")
    return int(major), int(minor)


def is_supported(version: tuple[int, int], minimum: tuple[int, int] = MIN_VERSION) -> bool:
    return version >= minimum


def version_label(version: tuple[int, int]) -> str:
    return f"{version[0]}.{version[1]}"


def unsupported_message(
    executable: str,
    current: tuple[int, int],
    minimum: tuple[int, int] = MIN_VERSION,
) -> str:
    return "\n".join(
        [
            (
                f"AI Brain requires Python {version_label(minimum)}+; "
                f"{executable} is Python {version_label(current)}."
            ),
            "Install Python 3.12 or 3.11, or run with an existing AI Brain virtualenv.",
            "",
            "Examples:",
            '  make -C ai-brain setup',
            '  make -C ai-brain init-repo TARGET_ROOT=..',
            '  PATH="ai-brain/.venv/bin:$PATH" make -C ai-brain init-repo TARGET_ROOT=..',
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Python version for AI Brain.")
    parser.add_argument(
        "--min-version",
        default=version_label(MIN_VERSION),
        help="Minimum supported Python version as major.minor.",
    )
    args = parser.parse_args()

    minimum = parse_version(args.min_version)
    current = (sys.version_info.major, sys.version_info.minor)
    if is_supported(current, minimum):
        return 0

    print(unsupported_message(sys.executable or "python", current, minimum), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
