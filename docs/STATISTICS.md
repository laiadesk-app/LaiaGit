# Statistics, downloads and visibility

Honest answer up front: **GitHub does NOT give you a list of people who
clone or download your repository.** That's a hard privacy boundary on
their side, not a feature we forgot to enable.

What you DO have is a set of aggregate counters and reach metrics that
together give you a clear picture of who is using LaiaGit and how. This
page documents what's available, where to find it, and what is impossible
no matter what.

---

## What you can measure (today, for free, on GitHub)

### 1. Repository-level traffic

Settings → **Insights → Traffic** on the repo page.

| Metric | What it tells you | Per-user? |
|---|---|---|
| **Views** (last 14 days) | How many times the repo page was visited | No, anonymous |
| **Unique visitors** (last 14 days) | Approximate distinct visitors | No, anonymous |
| **Clones** (last 14 days) | `git clone` operations | No |
| **Unique cloners** (last 14 days) | Approximate distinct clones | No |
| **Referring sites** | Where visitors came from (HN, Reddit, Twitter, etc.) | No |
| **Popular content** | Which files / paths got the most views | No |

> Direct link: `https://github.com/laiadesk-app/LaiaGit/graphs/traffic`

The 14-day window is a hard limit — if you want a longer history, export
it manually every two weeks (or use the [REST API](#api-access) below).

### 2. Stars, forks, watchers

These ARE per-user (they're public actions):

- **Stars**: `https://github.com/laiadesk-app/LaiaGit/stargazers` — full
  list of every account that starred the repo.
- **Forks**: `https://github.com/laiadesk-app/LaiaGit/network/members`
  — every fork, owner, and date.
- **Watchers**: visible on the repo header.

A fork is a strong signal that someone is actively building on top of
LaiaGit. A star is a weaker signal — bookmarking, basically.

### 3. Release downloads (when you cut binaries)

Once we ship pre-built binaries via **GitHub Releases**, every release
asset gets a per-asset download counter visible on the release page and
via API:

```bash
gh release view v0.1.0 --repo laiadesk-app/LaiaGit --json assets \
  -q '.assets[] | {name, downloadCount}'
```

That number is updated in near real-time. Still no per-user breakdown,
but it's the single most useful number for "did people install it?".

### 4. PyPI install counts (if/when we publish there)

If we ever publish LaiaGit to PyPI, install counts come from
[pypistats.org](https://pypistats.org) (mirrors Google BigQuery's PyPI
download dataset):

```bash
pip install pypistats
pypistats overall laiagit
pypistats python_minor laiagit  # which Python versions are using it
```

Again: aggregate only, no IPs, no users.

### 5. API access for everything above

For long-term tracking, automate the read instead of clicking the UI:

```bash
# Traffic (14-day window)
gh api repos/laiadesk-app/LaiaGit/traffic/views
gh api repos/laiadesk-app/LaiaGit/traffic/clones
gh api repos/laiadesk-app/LaiaGit/traffic/popular/referrers

# Star history
gh api repos/laiadesk-app/LaiaGit/stargazers \
  -H "Accept: application/vnd.github.star+json"

# Release download counts
gh api repos/laiadesk-app/LaiaGit/releases \
  -q '.[].assets[] | {tag: ., download_count, name}'
```

These endpoints need the `repo` scope on your token, which the `gh` CLI
already has when you log in normally.

---

## What you cannot measure (and why)

| You'd like to know… | Possible? | Why not |
|---|---|---|
| Who exactly cloned the repo | **No** | GitHub does not log clone identity |
| Who downloaded a release asset | **No** | Same |
| Who is running LaiaGit on their laptop right now | **No** | We have no telemetry, by design |
| Per-user usage patterns | **No** | Same |

LaiaGit ships **no telemetry, no phone-home, no analytics SDKs**. That's
a deliberate choice — the app reads your local Git repos, which is private
data. Adding telemetry to count installs would betray the trust users put
in a developer tool that runs on their workstation.

---

## What gives you the strongest signal of real usage

In rough order:

1. **Release asset downloads** (once we ship binaries).
2. **Active forks** — people building on top of LaiaGit.
3. **Issues opened** by accounts other than maintainers.
4. **Discussions activity**.
5. **Stars over time** (use a tool like
   [star-history.com](https://www.star-history.com) for the curve).

Stars alone are a vanity metric; pair them with forks + issues to know
whether stars are turning into actual usage.

---

## Related

- Privacy posture in [SECURITY.md](../SECURITY.md).
- Roadmap in [docs/plans/2026-05-01-laiagit-roadmap.md](plans/2026-05-01-laiagit-roadmap.md).
