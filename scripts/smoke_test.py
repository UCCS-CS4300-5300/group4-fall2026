"""
Smoke test for a running deployment (standard library only).

  python scripts/smoke_test.py https://<app>.onrender.com
      Checks health, creates a trip, answers every page, checks the summary,
      a wrong invite code (error path) and that the AI fails gracefully.
      Prints the trip's invite code and member name for the persistence check.

  python scripts/smoke_test.py https://<app>.onrender.com --rejoin CODE NAME
      After a redeploy: rejoins that trip as the same member and checks the
      saved answers are still there (data survived in Neon).

Add --expect-commit SHA to fail unless /healthz/ reports that commit.
Exit status is 0 only when every check passes.
"""
import argparse
import datetime as dt
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DESTINATION = "Denver"


class Site:  # pylint: disable=too-few-public-methods
    """A browser-like session: keeps cookies and sends Django's CSRF token."""

    def __init__(self, base):
        self.base = base.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def _csrf(self):
        return next((c.value for c in self.jar if c.name == "csrftoken"), "")

    def request(self, path, data=None, ajax=False):
        """(status, final path, body). Follows redirects; returns 4xx/5xx instead of raising."""
        body = None
        headers = {"Referer": self.base + "/", "User-Agent": "group4-smoke-test"}
        if data is not None:
            form = {**data, "csrfmiddlewaretoken": self._csrf()}
            body = urllib.parse.urlencode(form, doseq=True).encode()
            headers["X-CSRFToken"] = self._csrf()
        if ajax:
            headers["Accept"] = "application/json"
        req = urllib.request.Request(self.base + path, data=body, headers=headers)
        try:
            with self.opener.open(req, timeout=60) as resp:
                final_path = urllib.parse.urlparse(resp.geturl()).path
                return resp.status, final_path, resp.read().decode()
        except urllib.error.HTTPError as err:
            return err.code, path, err.read().decode(errors="replace")


class Checks:  # pylint: disable=too-few-public-methods
    """Prints PASS/FAIL lines and counts failures."""

    def __init__(self):
        self.failed = 0

    def check(self, ok, label, detail=""):
        """Record one result."""
        print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" ({detail})" if detail else ""))
        if not ok:
            self.failed += 1
        return ok


def health(site, checks, expect_commit):
    """/healthz/ answers, the database is reachable, and (optionally) the commit matches."""
    status, _, body = site.request("/healthz/")
    info = json.loads(body) if status in (200, 503) else {}
    checks.check(status == 200 and info.get("database") == "ok",
                 "health check: app and database up", f"HTTP {status}, commit {info.get('commit')}")
    if expect_commit:
        commit = info.get("commit", "")
        checks.check(commit.startswith(expect_commit) or expect_commit.startswith(commit or "-"),
                     "deployed commit matches", f"expected {expect_commit}, got {commit}")
    return info.get("commit")


def create_trip(site, checks):
    """Normal path: create a trip, answer every page, see it on the summary."""
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    trip_name, person = f"Smoke test {stamp}", "Smoke Tester"
    site.request("/")  # sets the CSRF cookie
    status, path, _ = site.request("/", {"tripName": trip_name, "personName": person})
    checks.check(status == 200 and path == "/destination/", "create a trip", f"landed on {path}")

    _, _, page = site.request("/destination/")
    match = re.search(r"\?code=([A-Z0-9]{8})", page)
    code = match.group(1) if match else ""
    checks.check(bool(code), "invite code shown on the destination page", code)

    start = dt.date.today() + dt.timedelta(days=60)
    for path, data in [
        ("/destination/", {"destinations": [DESTINATION]}),
        ("/schedule/", {"start_date": start.isoformat(),
                        "end_date": (start + dt.timedelta(days=3)).isoformat(),
                        "pace": "balanced"}),
        ("/budget/", {"budget_amount": "1200", "currency": "USD"}),
        ("/activities/", {"activities": ["hiking"]}),
    ]:
        status, landed, _ = site.request(path, data)
        checks.check(status == 200 and landed != path, f"save answers on {path}",
                     f"HTTP {status}, now on {landed}")

    status, _, summary = site.request("/summary/")
    checks.check(status == 200 and trip_name in summary and DESTINATION in summary,
                 "summary shows the trip and its answers")
    return trip_name, person, code


def wrong_code_is_rejected(base, checks):
    """Error path: joining with a code that doesn't exist."""
    other = Site(base)
    other.request("/join/")
    status, _, body = other.request("/join/", {"invite_code": "ZZZZZZZZ", "person_name": "Nobody"})
    checks.check(status == 400 and "Invalid invitation code." in body,
                 "error path: a wrong invite code is rejected with a message",
                 f"HTTP {status}")


def ai_fails_gracefully(site, checks, wait_seconds):
    """The AI run ends with results or a clear failure, and the page still loads."""
    status, _, body = site.request("/ai/run/", {}, ajax=True)
    checks.check(status == 200, "AI run endpoint answers", f"HTTP {status}")
    state = json.loads(body) if status == 200 else {}
    deadline = time.time() + wait_seconds
    while state.get("status") == "running" and time.time() < deadline:
        time.sleep(3)
        _, _, body = site.request("/ai/status/", ajax=True)
        state = json.loads(body)
    checks.check(state.get("status") in {"done", "failed"},
                 "AI run finishes (results, or 'AI unavailable' without crashing)",
                 f"{state.get('status')}: {state.get('error') or 'results ready'}")
    status, _, _ = site.request("/ai-output/")
    checks.check(status == 200, "AI suggestions page loads", f"HTTP {status}")


def rejoin(site, checks, code, person):
    """Persistence: the trip and its answers are still there after a redeploy."""
    site.request("/join/")
    status, path, _ = site.request("/join/", {"invite_code": code, "person_name": person})
    checks.check(status == 200 and path == "/destination/",
                 "rejoin the saved trip after redeploy", f"landed on {path}")
    status, _, summary = site.request("/summary/")
    checks.check(status == 200 and DESTINATION in summary and "1200" in summary,
                 "saved answers survived the redeploy (still in Neon)")


def main(argv=None):
    """Run the checks; exit status 1 if any fail."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base_url")
    parser.add_argument("--rejoin", nargs=2, metavar=("CODE", "NAME"))
    parser.add_argument("--expect-commit", default="")
    parser.add_argument("--ai-wait", type=int, default=120, help="seconds to wait for the AI run")
    args = parser.parse_args(argv)

    site, checks = Site(args.base_url), Checks()
    print(f"Smoke test of {site.base} at {dt.datetime.now().isoformat(timespec='seconds')}")
    commit = health(site, checks, args.expect_commit)
    if args.rejoin:
        rejoin(site, checks, *args.rejoin)
    else:
        _, person, code = create_trip(site, checks)
        wrong_code_is_rejected(args.base_url, checks)
        ai_fails_gracefully(site, checks, args.ai_wait)
        print(f"\nFor the persistence check after the next redeploy:\n"
              f"  python scripts/smoke_test.py {site.base} --rejoin {code} \"{person}\"")
    result = "ALL CHECKS PASSED" if not checks.failed else f"{checks.failed} CHECK(S) FAILED"
    print(f"\n{result} (commit {commit})")
    return 1 if checks.failed else 0


if __name__ == "__main__":
    sys.exit(main())
