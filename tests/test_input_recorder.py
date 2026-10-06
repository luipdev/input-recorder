import ast

import pytest

from input_recorder.codegen import generate_script
from input_recorder.events import Event, load, save, thin_moves

SAMPLE = [
    Event(0.0, "key_down", key="char:a"),
    Event(0.08, "key_up", key="char:a"),
    Event(1.1, "key_down", key="special:up"),
    Event(1.25, "key_up", key="special:up"),
    Event(1.3, "move", x=10, y=20),
    Event(1.4, "mouse_down", x=10, y=20, button="left"),
    Event(1.45, "mouse_up", x=10, y=20, button="left"),
]


def test_generated_script_is_valid_python():
    source = generate_script(SAMPLE)
    ast.parse(source)  # raises SyntaxError if the generator is broken


def test_generated_script_keeps_timing_and_actions():
    source = generate_script(SAMPLE)
    assert "keyboard.press('a')" in source
    assert "keyboard.release(Key.up)" in source
    assert "time.sleep(1.02)" in source
    assert "mouse.press(Button.left)" in source


def test_quotes_and_backslashes_are_escaped():
    events = [Event(0, "key_down", key="char:'"), Event(0.1, "key_down", key="char:\\")]
    source = generate_script(events)
    ast.parse(source)
    assert "keyboard.press(\"'\")" in source


@pytest.mark.parametrize(
    "key",
    ["special:up); import os; os.system('x'", "special:", "char:ab", "other:a", "a", None],
)
def test_bad_keys_are_rejected(key):
    with pytest.raises(ValueError):
        Event(0, "key_down", key=key)


def test_bad_button_and_kind_are_rejected():
    with pytest.raises(ValueError):
        Event(0, "mouse_down", x=1, y=1, button="side")
    with pytest.raises(ValueError):
        Event(0, "teleport")


def test_thin_moves_keeps_clicks_and_last_move_before_click():
    events = [Event(i * 0.001, "move", x=i, y=i) for i in range(50)]
    events.append(Event(0.06, "mouse_down", x=49, y=49, button="left"))
    thinned = thin_moves(events, min_interval=0.02)
    assert len(thinned) < len(events)
    assert thinned[-1].kind == "mouse_down"
    assert thinned[-2] == events[49]  # the move right before the click survives


def test_json_roundtrip(tmp_path):
    path = tmp_path / "session.json"
    save(SAMPLE, path)
    assert load(path) == SAMPLE
