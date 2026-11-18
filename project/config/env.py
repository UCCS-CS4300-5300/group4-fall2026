"""
Read deployment settings from environment variables.

Locally and in CI nothing needs to be set: the defaults give the usual
development setup (DEBUG on, SQLite). Render sets the variables below.
"""
import os

TRUE_WORDS = {"1", "true", "yes", "on"}
FALSE_WORDS = {"0", "false", "no", "off", ""}


def env_bool(name, default, environ=None):
    """
    A true/false setting. Parsed by word, because bool("False") is True in
    Python, which would leave DEBUG on in production.
    """
    environ = os.environ if environ is None else environ
    raw = environ.get(name)
    if raw is None:
        return default
    word = raw.strip().lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ValueError(f"{name} must be true or false, not {raw!r}")


def env_list(name, environ=None):
    """A comma-separated setting as a list, ignoring spaces and empty items."""
    environ = os.environ if environ is None else environ
    return [item.strip() for item in environ.get(name, "").split(",") if item.strip()]


def allowed_hosts(debug, environ=None):
    """
    Host names the site answers to: DJANGO_ALLOWED_HOSTS plus the name Render
    gives the service (RENDER_EXTERNAL_HOSTNAME). Any host in development.
    """
    environ = os.environ if environ is None else environ
    hosts = env_list("DJANGO_ALLOWED_HOSTS", environ)
    render_host = environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if render_host:
        hosts.append(render_host)
    if not hosts and debug:
        hosts = ["*"]
    return hosts


def csrf_trusted_origins(environ=None):
    """HTTPS origins allowed to submit forms: the Render URL plus DJANGO_CSRF_TRUSTED_ORIGINS."""
    environ = os.environ if environ is None else environ
    origins = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", environ)
    render_host = environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if render_host:
        origins.append(f"https://{render_host}")
    return origins
