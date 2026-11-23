# Group 4 Trip Planner

A group trip planner. One person creates a trip and shares an invite link; each member enters destinations, dates, budget and activities. The summary page combines everyone's answers, and an AI (Ollama, `llama3.1`) suggests a destination, activities and a budget estimate in the background.

## Run it locally
From this `project/` folder, with Python 3.12:

```
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt        # Windows: .venv\Scripts\python.exe
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/, create a trip, then open the invite link in a private window to add a second member. No environment variables are needed locally: the app uses SQLite and `DEBUG` is on.

**AI (optional):** install [Ollama](https://ollama.com/download), then `ollama pull llama3.1:latest`. Without it the app still works and the AI section says "AI unavailable" with a Try again button.

## Tests
```
python -m pytest -q
```
Ollama is always faked in tests, so no model server is needed. CI (`.github/workflows/quality.yml`) runs the same tests on every pull request with `config/quality_test_settings.py` (an in-memory database), plus coverage, Pylint and Radon. On a push to `main` it also produces the course AI quality report.

## Deploying to Render + Neon
Render runs the app with Gunicorn; Neon provides the PostgreSQL database. Settings come from environment variables (`config/settings.py`, `config/env.py`).

**Neon:** create a project, then copy its connection string (it ends in `?sslmode=require`). Keep it secret; never commit it or use it locally or in CI.

**Render** → New → Web Service → this repository:

| Setting | Value |
| --- | --- |
| Branch | `main` |
| Root Directory | `project` |
| Runtime | Python 3 (version from `.python-version`: 3.12) |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn config.wsgi:application` |
| Instance type | Free |
| Auto-Deploy | **After CI Checks Pass** |

Environment variables:

| Name | Value |
| --- | --- |
| `DATABASE_URL` | the Neon connection string |
| `DJANGO_SECRET_KEY` | a long random value (Render's "Generate" button) |
| `DJANGO_DEBUG` | `False` |
| `PYTHON_VERSION` | `3.12.3` (only if Render ignores `.python-version`) |

Render supplies `RENDER_EXTERNAL_HOSTNAME` (added to allowed hosts and trusted form origins) and `RENDER_GIT_COMMIT` (shown by `/healthz/`). For a custom domain, also set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated).

`build.sh` installs `requirements-render.txt` (the app's requirements plus `psycopg` and `gunicorn`), collects static files and applies migrations to Neon. Each deploy therefore migrates the live database; review new migrations before merging to `main`.

## Check a deployment
From the repository root:

```
python scripts/smoke_test.py https://<app>.onrender.com --expect-commit <sha>
```

It checks `/healthz/` (database reachable, deployed commit), creates a trip, answers every page, checks the summary, checks that a wrong invite code is rejected, and checks that the AI finishes or fails cleanly. It prints a `--rejoin CODE NAME` command: run that after the next redeploy to confirm the saved data is still there.

`https://<app>.onrender.com/healthz/` alone returns `{"status": "ok", "commit": "<sha>", "database": "ok"}`, or HTTP 503 if the database can't be reached.

## Known limitations
- **AI on Render uses Ollama Cloud.** Set `OLLAMA_HOST=https://ollama.com`, `OLLAMA_API_KEY` (Render only, never in code) and `OLLAMA_MODEL` on Render. If the account has no credits or the service is down, the AI section shows "AI unavailable" with Try again, and the rest of the app keeps working.
- **Free-tier sleep.** Render Free stops the service when idle; the first request after that can take about a minute.
- **No passwords.** Anyone with a trip's invite code can join it, and rejoining with an existing member's name continues as that member.

## Troubleshooting
| Symptom | Likely cause and fix |
| --- | --- |
| Render build fails at `pip install` | A dependency doesn't support Python 3.12, or `.python-version` was ignored: set `PYTHON_VERSION`. |
| `Set DJANGO_SECRET_KEY when DJANGO_DEBUG is false` | Add `DJANGO_SECRET_KEY` on Render. |
| HTTP 400 Bad Request on every page | The host isn't allowed: check the service URL, or set `DJANGO_ALLOWED_HOSTS`. |
| "CSRF verification failed" on forms | The site's origin isn't trusted: set `DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-domain>`. |
| `/healthz/` returns 503 | Neon is unreachable: check `DATABASE_URL`, and that the Neon project isn't suspended. |
| Admin page has no styling | `collectstatic` didn't run: check the build log for `build.sh`. |
| A deploy didn't happen after a merge | Auto-Deploy waits for CI: open the commit's checks on GitHub and fix the failing one. |
| Locally, AI says unavailable | Start Ollama and run `ollama pull llama3.1:latest`, then click Try again. |

Use `DJANGO_DEBUG=True` on Render only briefly for debugging. It shows error details to everyone.
