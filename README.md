# input-recorder

Record keyboard and mouse input, then replay it or turn it into a standalone
Python script. Useful for repetitive desktop tasks.

```bash
python -m input_recorder record session.json          # F9 stops
python -m input_recorder play session.json --speed 1.5
python -m input_recorder generate session.json macro.py
python macro.py                                        # runs without input-recorder installed
```

## How it works

1. **Record.** pynput listeners capture key presses, clicks and mouse moves with
   timestamps from a monotonic clock (`perf_counter`).
2. **Store as data.** Events are saved as JSON, not code, so a recording can be
   replayed, trimmed by hand or regenerated later.
3. **Thin the moves.** Mouse listeners fire hundreds of move events per second.
   Moves closer than 20 ms are dropped, except the one right before a click.
4. **Replay or generate.** `play` replays directly. `generate` writes a script
   that only needs pynput, keeping the original timing with `time.sleep()`.

## Safety of generated code

The generator writes Python from a file, so a crafted recording must not be able
to inject code. Characters are written with `repr()`, special keys must be plain
identifiers (`special:enter`), and anything else is rejected when the recording
is loaded. A test tries an injection payload and checks that it fails.

## Install and test

```bash
pip install -e ".[record]"   # pynput
pip install -e ".[dev]"
pytest
```

## Background

Version 1 was one of the first tools I wrote while learning Python. It wrote the
recording straight into Python source, as text, inside the recorder; it was tied
to one window title, and the keyboard-only mode was a copy of the whole file.
This version separates recording, storage and code generation, and adds the
injection-safe generator and tests.

## License

MIT
