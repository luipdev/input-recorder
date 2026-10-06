"""Record keyboard and mouse input, replay it, or generate a script from it."""

from .codegen import generate_script
from .events import Event, load, save, thin_moves

__all__ = ["Event", "generate_script", "load", "save", "thin_moves"]
__version__ = "2.0.0"
