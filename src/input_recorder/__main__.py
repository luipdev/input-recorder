"""Command line tool.

    python -m input_recorder record session.json            (F9 stops)
    python -m input_recorder record session.json --keyboard-only
    python -m input_recorder generate session.json macro.py
    python -m input_recorder play session.json --speed 1.5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .codegen import generate_script
from .events import load, save, thin_moves


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="input-recorder")
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="record input to a JSON file")
    rec.add_argument("output")
    rec.add_argument("--keyboard-only", action="store_true")
    rec.add_argument("--stop-key", default="f9")
    rec.add_argument("--countdown", type=float, default=3.0)

    gen = sub.add_parser("generate", help="turn a recording into a Python script")
    gen.add_argument("recording")
    gen.add_argument("output")
    gen.add_argument("--start-delay", type=float, default=2.0)

    play = sub.add_parser("play", help="replay a recording")
    play.add_argument("recording")
    play.add_argument("--speed", type=float, default=1.0)
    play.add_argument("--countdown", type=float, default=3.0)

    args = parser.parse_args(argv)

    try:
        if args.command == "record":
            from .recorder import record

            print(f"Recording in {args.countdown:g}s. Press {args.stop_key.upper()} to stop.")
            time.sleep(args.countdown)
            events = thin_moves(record(args.stop_key, mouse=not args.keyboard_only))
            save(events, args.output)
            print(f"Saved {len(events)} events to {args.output}")

        elif args.command == "generate":
            events = load(args.recording)
            Path(args.output).write_text(generate_script(events, args.start_delay), encoding="utf-8")
            print(f"Wrote {args.output} ({len(events)} events)")

        elif args.command == "play":
            from .recorder import replay

            if args.speed <= 0:
                raise ValueError("speed must be positive")
            events = load(args.recording)
            print(f"Replaying {len(events)} events in {args.countdown:g}s...")
            time.sleep(args.countdown)
            replay(events, args.speed)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
