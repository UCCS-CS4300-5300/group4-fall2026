# In-Class Activity — Git Team Workflow

**Target time: 60–65 minutes of required work + ~10 minutes of buffer**

Today your team will practice the kind of Git workflow that matters when several people are changing the same software at the same time.

The goal is not simply to get code into `main`.

The goal is to leave behind an engineering trail that another person can reconstruct:

**baseline → branch → change → test → commit → pull request → review → merge → conflict → recovery**

Work through this page **in order**. Do not skip ahead.

---

# IMPORTANT — Use Your Team Project Repository

The public `git-team-workflow-lab` repository is **starter material only**.

**Do not create branches or pull requests in the public starter repository.** Every team in the class would collide with every other team.

Your team will perform the entire activity inside **your own team project repository**.

Before Stage 1:

1. Open your team's existing project repository.
2. In that repository, create a folder named:

```text
git-team-workflow-lab/
```

3. Download/copy the starter files from:

https://github.com/UCCS-CS4300-5300/git-team-workflow-lab

4. Put the starter files inside `git-team-workflow-lab/` in **your project repository**.

Your repository should contain something like:

```text
your-team-project/
├── git-team-workflow-lab/
│   ├── app.py
│   ├── test_app.py
│   └── requirements.txt
└── ...your other project files...
```

**Do not clone the public lab repository inside your project repository.** That would create a Git repository inside another Git repository. Copy/download the files instead.

One team member should commit the untouched starter to your team's `main` branch:

```bash
git add git-team-workflow-lab/
git commit -m "Add Git workflow lab baseline"
git push
```

Then **every team member pulls that same baseline before continuing**.

All branches, commits, PRs, merges, conflicts, and recovery work in this activity happen in **your team's project repository**, not in the public starter.

> **SETUP CHECKPOINT — Do not continue until the lab files are committed to your team repository's `main` branch and everyone has pulled the same baseline.**

---

## Team Roles

Assign these roles before beginning. If your team has fewer people, combine roles. If you have more people, pair on one or more roles.

- **Developer A** — makes Change A and opens PR A
- **Developer B** — makes Change B and opens PR B
- **Reviewer** — reviews PR A and PR B
- **Recovery Driver** — leads the history/recovery portion later

Rotate who is physically driving the keyboard. This is not a one-laptop spectator activity.

---

# Stage 1 — Establish the Baseline

Everyone should open **your team's project repository** in their own environment and make sure `main` is current:

```bash
git switch main
git pull
git status
```

Move into the lab folder:

```bash
cd git-team-workflow-lab
```

Install the test dependency if needed:

```bash
pip install -r requirements.txt
```

Run the tests:

```bash
python -m pytest
```

You should begin with all tests passing.

Now record the current commit:

```bash
git log -1 --oneline
```

As a team, answer verbally:

- What evidence do you have that the starting system works?
- What commit are you starting from?

> **CHECKPOINT 1 — Do not continue until everyone is starting from the same `main` and the tests pass.**

---

# Stage 2 — Create Two Parallel Changes

Developer A and Developer B must both branch from the same current version of `main` **before either PR is merged**.

First, both developers run from the project repository:

```bash
git switch main
git pull
git status
```

## Developer A — Change A

Create a branch:

```bash
git switch -c feature/audience-description
```

In `git-team-workflow-lab/app.py`, change the `description` value inside `PROJECT_INFO` so the description clearly says the tool is **for student software teams**.

A reasonable result would communicate this meaning:

> Trailhead is a project planning tool for student software teams.

You do not have to use that exact sentence, but your description must include the intended audience.

From the lab folder, run the tests:

```bash
python -m pytest
```

Then inspect what changed:

```bash
git diff
```

Commit and push:

```bash
git add git-team-workflow-lab/app.py
git commit -m "Clarify Trailhead target users"
git push -u origin feature/audience-description
```

## Developer B — Change B

**Developer B should NOT pull Developer A's work.** Your branch must still come from the original baseline.

Create a branch:

```bash
git switch -c feature/value-description
```

In `git-team-workflow-lab/app.py`, change the same `description` value inside `PROJECT_INFO` so the description clearly says the tool helps teams **coordinate work and surface blockers**.

A reasonable result would communicate this meaning:

> Trailhead helps teams coordinate work and surface blockers.

Again, exact wording is up to you, but both ideas must be present.

Run the tests:

```bash
python -m pytest
```

Inspect the change:

```bash
git diff
```

Commit and push:

```bash
git add git-team-workflow-lab/app.py
git commit -m "Describe Trailhead coordination value"
git push -u origin feature/value-description
```

> **CHECKPOINT 2 — Both branches must exist remotely before anyone merges anything.**

---

# Stage 3 — PR A: The Happy Path

Developer A opens a pull request in **your team project repository** from:

`feature/audience-description` → `main`

The PR description should include:

- **What changed?**
- **Why was it needed?**
- **How was it verified?**

The Reviewer should inspect the **Files changed** tab, confirm the requested behavior is present, and check that the tests were run.

The Reviewer should leave a real review comment or approval—not just click through without reading.

Then merge PR A.

After merge, everyone except Developer B may update `main`:

```bash
git switch main
git pull
```

> **CHECKPOINT 3 — PR A must be merged before Developer B updates their branch.**

---

# Stage 4 — PR B: The Conflict

Developer B now opens a pull request in **your team project repository** from:

`feature/value-description` → `main`

GitHub should indicate that the branch cannot be merged cleanly.

Good. That is intentional.

Before touching anything, look at the two requirements again:

- Change A: identify **student software teams** as the audience.
- Change B: explain that Trailhead helps teams **coordinate work and surface blockers**.

Ask:

> Which version is correct?

The answer is: **both requirements are legitimate.**

Git can tell you that the histories conflict. Git cannot decide what the final product should mean.

Developer B should bring the latest `main` into the branch:

```bash
git switch feature/value-description
git fetch origin
git merge origin/main
```

Git should report a conflict in `git-team-workflow-lab/app.py`.

Open the file and find markers like:

```text
<<<<<<< HEAD
...
=======
...
>>>>>>> origin/main
```

Resolve the conflict by writing **one final description that preserves BOTH stakeholder intentions**.

Do **not** simply choose one side.

Remove all conflict markers, save the file, then run from the lab folder:

```bash
python -m pytest
```

Check Git's view of the conflict resolution:

```bash
git status
git diff
```

Then commit and push the resolution:

```bash
git add git-team-workflow-lab/app.py
git commit -m "Resolve project description conflict"
git push
```

Return to PR B. The Reviewer should now review the final result and confirm that **both requirements survived the merge**.

Merge PR B.

> **CHECKPOINT 4 — Do not continue until `main` contains one description that satisfies both requests and all tests pass.**

---

# Stage 5 — Introduce a Bad Change

Now switch drivers. The **Recovery Driver should NOT be the person who makes the bad change.**

One team member updates `main`:

```bash
git switch main
git pull
```

Create a branch:

```bash
git switch -c bug/risk-threshold-change
```

Open `git-team-workflow-lab/app.py`.

Change this line:

```python
if open_blockers >= 4:
```

to:

```python
if open_blockers >= 5:
```

Pretend this came from a rushed misunderstanding of a stakeholder request.

Commit the change **without changing the tests**:

```bash
git add git-team-workflow-lab/app.py
git commit -m "Adjust high risk threshold"
git push -u origin bug/risk-threshold-change
```

Open a PR and merge it into `main`.

Now everyone updates `main` and, from the lab folder, runs:

```bash
git switch main
git pull
python -m pytest
```

Something should fail.

Do **not** fix the line manually.

Your job now is to treat the repository as evidence.

> **CHECKPOINT 5 — The failure is intentional. From this point forward, do not repair the code by simply editing it.**

---

# Stage 6 — Repository Forensics

The Recovery Driver takes over.

Assume you do not remember exactly what changed.

Start with:

```bash
git log --oneline --decorate -8
```

Find the suspicious recent commit.

Inspect it:

```bash
git show <commit-sha>
```

You can also compare versions:

```bash
git diff <older-commit>..<newer-commit>
```

As a team, identify:

- Which commit introduced the failure?
- What exactly changed?
- Why does the existing test make that change suspicious?

Do not move on until everyone can point to the evidence.

---

# Stage 7 — Visit an Earlier Version

Now inspect the repository **before** the bad change without rewriting history.

Use the parent of the bad commit:

```bash
git switch --detach <bad-commit-sha>^
```

From the lab folder, run:

```bash
python -m pytest
```

The tests should pass again.

Look at `app.py` and confirm that you are viewing an earlier state of the repository.

Now return to current `main`:

```bash
git switch main
```

Run:

```bash
git status
```

As a team, explain the difference between:

- **looking at an older version**, and
- **changing the shared project's current history**.

---

# Stage 8 — Recover Without Erasing the Evidence

You know which commit introduced the defect.

Undo it with:

```bash
git revert <bad-commit-sha>
```

Git will create a **new commit** that reverses the earlier one.

If Git opens an editor for the revert commit message, keep the default message and save/close the editor.

From the lab folder, run:

```bash
python -m pytest
```

The tests should pass.

Push the recovery:

```bash
git push
```

Notice what you did **not** do: you did not erase the bad commit from history.

The repository now records both facts:

1. the bad change happened;
2. the team intentionally reversed it.

That is useful engineering evidence.

---

# Stage 9 — Read the Story Your Repository Tells

Run:

```bash
git log --oneline --graph --decorate --all
```

Look at the history your team created.

You should be able to identify:

- the lab baseline;
- Developer A's branch;
- Developer B's parallel branch;
- the first merge;
- the conflict resolution;
- the bad change;
- the revert/recovery.

Then answer these as a team:

1. **Why couldn't Git decide the correct conflict resolution for you?**
2. **What information did you need beyond the conflicting lines themselves?**
3. **What evidence helped you identify the bad change?**
4. **Why was `git revert` useful here instead of pretending the bad commit never existed?**
5. **What could a teammate who missed class learn just from this repository history?**
6. **Which parts of this workflow genuinely reduce coordination risk, and which parts could become process theater if done carelessly?**

## Final idea

Git stores code, but that is not all it stores.

A well-used repository preserves **evidence about how the software became what it is**.

The public lab repository was only the starter. **The engineering trail you created today should live in your team's project repository.**
