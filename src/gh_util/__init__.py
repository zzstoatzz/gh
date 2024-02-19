from .settings import settings

from rich.traceback import install

install(show_locals=settings.test_mode)
