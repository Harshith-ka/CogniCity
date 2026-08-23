"""Shared slowapi limiter instance — a single object main.py registers on the app
and individual routers (auth.py) decorate their endpoints with, so importing this
module never has to reach back into main.py (which imports the routers)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
