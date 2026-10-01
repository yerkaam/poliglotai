"""Settings for pytest: the development defaults (debug on, local cache, development key)."""

import os

os.environ.setdefault("DJANGO_DEBUG", "1")

from .settings import *  # noqa: E402, F403
