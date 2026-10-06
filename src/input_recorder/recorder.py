"""Live recording and replay with pynput (imported only when used)."""

from __future__ import annotations

import threading
import time

from .events import Event


def _key_name(key) -> str | None:
    """"char:a" for printable keys, "special:enter" for named keys.

    Returns None for keys pynput only knows by virtual-key code (some media or
    vendor keys); those are skipped instead of crashing the recording.
    """
    char = getattr(key, "char", None)
    if char is not None and len(char) == 1:
        return f"char:{char}"
    name = getattr(key, "name", None)
    return f"special:{name}" if name else None


def record(stop_key: str = "f9", mouse: bool = True) -> list[Event]:
    """Records keyboard (and optionally mouse) input until ``stop_key`` is released."""
    from pynput import keyboard
    from pynput import mouse as pmouse

    events: list[Event] = []
    lock = threading.Lock()
    start = time.perf_counter()
    stop = getattr(keyboard.Key, stop_key)

    def add(**kw) -> None:
        with lock:
            events.append(Event(t=time.perf_counter() - start, **kw))

    def on_press(key):
        name = _key_name(key)
        if key != stop and name:
            add(kind="key_down", key=name)

    def on_release(key):
        if key == stop:
            return False
        name = _key_name(key)
        if name:
            add(kind="key_up", key=name)
        return None

    def on_click(x, y, button, pressed):
        add(kind="mouse_down" if pressed else "mouse_up", x=int(x), y=int(y), button=button.name)

    def on_move(x, y):
        add(kind="move", x=int(x), y=int(y))

    mouse_listener = pmouse.Listener(on_click=on_click, on_move=on_move) if mouse else None
    if mouse_listener:
        mouse_listener.start()
    with keyboard.Listener(on_press=on_press, on_release=on_release) as kb:
        kb.join()
    if mouse_listener:
        mouse_listener.stop()
    return events


def replay(events: list[Event], speed: float = 1.0) -> None:
    """Replays events directly, without generating a script."""
    from pynput.keyboard import Controller as Keyboard, Key, KeyCode
    from pynput.mouse import Button, Controller as Mouse

    kb, ms = Keyboard(), Mouse()

    def to_key(name: str):
        prefix, value = name.split(":", 1)
        return KeyCode.from_char(value) if prefix == "char" else getattr(Key, value)

    previous = None
    for ev in events:
        if previous is not None:
            time.sleep(max(0.0, (ev.t - previous) / speed))
        previous = ev.t
        if ev.kind == "key_down":
            kb.press(to_key(ev.key))
        elif ev.kind == "key_up":
            kb.release(to_key(ev.key))
        else:
            ms.position = (ev.x, ev.y)
            if ev.kind == "mouse_down":
                ms.press(getattr(Button, ev.button))
            elif ev.kind == "mouse_up":
                ms.release(getattr(Button, ev.button))
