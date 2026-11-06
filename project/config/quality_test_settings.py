"""CI/test settings only. Never use these as Render production settings."""
from .settings import *  # noqa: F403
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
