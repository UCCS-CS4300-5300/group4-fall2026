#!/usr/bin/env bash
# Replays the test suite at every commit on a branch and prints one line per commit.
# Research evidence: the same method gives the Milestone 1 baseline and the follow-ups.
#
# Usage, from the repository root, with the project's virtual environment active:
#   bash replay_tests.sh [START_COMMIT] [BRANCH]
# Defaults: START_COMMIT=d52533e (last commit before Sprint 2), BRANCH=origin/sprint-2
#
# Each commit is checked out in a temporary worktree, so your working copy is untouched.
set -u
START="${1:-d52533e}"
BRANCH="${2:-origin/sprint-2}"
WT="$(mktemp -d)/replay"

git fetch -q origin
git worktree add -q --detach "$WT" "$BRANCH"
trap 'git worktree remove --force "$WT"' EXIT

printf "commit\tdate\tauthor\tmigrations\ttests\tsubject\n"
for c in $(git rev-list --reverse --topo-order "$START..$BRANCH"); do
  git -C "$WT" checkout -q --force "$c" && git -C "$WT" clean -fdq
  if [ -d "$WT/project" ]; then
    mig=$(cd "$WT/project" && python manage.py makemigrations --check --dry-run >/dev/null 2>&1 && echo clean || echo DIRTY)
    res=$(cd "$WT/project" && timeout 300 python -m pytest -q -p no:cacheprovider 2>&1 | tail -1)
  else
    mig="-"; res="-"
  fi
  printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$(git log -1 --format=%h "$c")" \
    "$(git log -1 --format=%ad --date=format:'%Y-%m-%d %H:%M' "$c")" \
    "$(git log -1 --format=%an "$c")" \
    "$mig" "$res" \
    "$(git log -1 --format=%s "$c" | cut -c1-60)"
done
