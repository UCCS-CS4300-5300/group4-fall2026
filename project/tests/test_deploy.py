"""
Deployment settings and health check (Joseph): what Render relies on.
Production settings are checked in a separate Python process, because
settings are read once when Django starts.
"""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from django.urls import reverse

from config.env import allowed_hosts, csrf_trusted_origins, env_bool, env_list

PROJECT = Path(__file__).resolve().parents[1]
SECRET = secrets.token_urlsafe(50)  # random, like the real one on Render
PROD_ENV = {
    "DJANGO_DEBUG": "False",
    "DJANGO_SECRET_KEY": SECRET,
    "RENDER_EXTERNAL_HOSTNAME": "group4.onrender.com",
}


def run_django(code, extra_env):
    """
    Run code in a fresh process with DJANGO_SETTINGS_MODULE=config.settings.
    It only reads settings and doesn't start Django, so no database driver
    (psycopg) is needed: CI and local setups don't install it.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "RENDER_", "DATABASE_URL"))}
    env.update({"DJANGO_SETTINGS_MODULE": "config.settings", **extra_env})
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT, env=env, capture_output=True, text=True, check=False,
    )


# ---- Reading environment variables ------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("False", False), ("false", False), ("0", False), ("no", False), (" off ", False), ("", False),
    ("True", True), ("1", True), ("yes", True), ("ON", True),
])
def test_env_bool_reads_words_not_python_truthiness(raw, expected):
    assert env_bool("DJANGO_DEBUG", True, {"DJANGO_DEBUG": raw}) is expected


def test_env_bool_uses_the_default_when_unset():
    assert env_bool("DJANGO_DEBUG", True, {}) is True
    assert env_bool("DJANGO_DEBUG", False, {}) is False


def test_env_bool_rejects_a_typo_instead_of_guessing():
    with pytest.raises(ValueError, match="DJANGO_DEBUG"):
        env_bool("DJANGO_DEBUG", True, {"DJANGO_DEBUG": "Flase"})


def test_env_list_splits_on_commas_and_ignores_blanks():
    assert env_list("H", {"H": " a.com, ,b.com ,"}) == ["a.com", "b.com"]
    assert env_list("H", {}) == []


def test_allowed_hosts_include_the_render_hostname():
    environ = {"DJANGO_ALLOWED_HOSTS": "trips.example.com", "RENDER_EXTERNAL_HOSTNAME": "group4.onrender.com"}
    assert allowed_hosts(False, environ) == ["trips.example.com", "group4.onrender.com"]


def test_allowed_hosts_are_open_only_in_development():
    assert allowed_hosts(True, {}) == ["*"]
    assert allowed_hosts(False, {}) == []


def test_csrf_trusts_the_render_url_over_https():
    assert csrf_trusted_origins({"RENDER_EXTERNAL_HOSTNAME": "group4.onrender.com"}) == [
        "https://group4.onrender.com"
    ]


# ---- Production settings, in a fresh process --------------------------------

def test_production_settings_pass_djangos_deploy_checklist():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "RENDER_", "DATABASE_URL"))}
    env.update({"DJANGO_SETTINGS_MODULE": "config.settings", **PROD_ENV})
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
        cwd=PROJECT, env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_production_refuses_to_start_without_a_secret_key():
    result = run_django("from django.conf import settings\nprint(settings.DEBUG)", {"DJANGO_DEBUG": "False"})
    assert result.returncode != 0
    assert "Set DJANGO_SECRET_KEY" in result.stderr


def test_production_is_locked_down():
    code = (
        "from django.conf import settings as s\n"
        "print(__import__('json').dumps({'debug': s.DEBUG, 'hosts': s.ALLOWED_HOSTS,"
        " 'csrf': s.CSRF_TRUSTED_ORIGINS, 'secure': s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE,"
        " 'whitenoise': 'whitenoise.middleware.WhiteNoiseMiddleware' in s.MIDDLEWARE}))"
    )
    result = run_django(code, PROD_ENV)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "debug": False,
        "hosts": ["group4.onrender.com"],
        "csrf": ["https://group4.onrender.com"],
        "secure": True,
        "whitenoise": True,
    }


def test_database_url_selects_postgres_with_ssl():
    code = (
        "from django.conf import settings as s\n"
        "db = s.DATABASES['default']\n"
        "print(db['ENGINE'], db['HOST'], db['NAME'], db['OPTIONS'].get('sslmode'))"
    )
    url = "postgresql://app:pw@ep-cool-1.us-east-2.aws.neon.tech/neondb?sslmode=require"
    result = run_django(code, {**PROD_ENV, "DATABASE_URL": url})
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [
        "django.db.backends.postgresql", "ep-cool-1.us-east-2.aws.neon.tech", "neondb", "require",
    ]


def test_without_database_url_development_uses_sqlite():
    result = run_django("from django.conf import settings as s\nprint(s.DATABASES['default']['ENGINE'])", {})
    assert result.stdout.strip() == "django.db.backends.sqlite3"


# ---- Health check -----------------------------------------------------------

@pytest.mark.django_db
def test_healthz_reports_ok_and_the_deployed_commit(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234")
    r = client.get(reverse("healthz"))
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "commit": "abc1234", "database": "ok"}


@pytest.mark.django_db
def test_healthz_reports_local_outside_render(client, monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert client.get(reverse("healthz")).json()["commit"] == "local"


@pytest.mark.django_db
def test_healthz_returns_503_when_the_database_is_down(client, monkeypatch):
    from django.db import OperationalError

    from core import health

    class BrokenConnection:
        def cursor(self):
            raise OperationalError("connection refused")

    monkeypatch.setattr(health, "connection", BrokenConnection())
    r = client.get(reverse("healthz"))
    assert r.status_code == 503
    assert r.json()["database"] == "unreachable"


@pytest.mark.django_db
def test_healthz_only_accepts_get(client):
    assert client.post(reverse("healthz")).status_code == 405
