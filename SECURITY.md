# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in LaiaGit, **please do not open a
public GitHub issue**. Instead, report it privately:

- **Preferred:** GitHub's [private security advisory](https://github.com/laiadesk-app/LaiaGit/security/advisories/new)
  form (visible only to maintainers).
- **Or by email:** `info@laiadesk.com` with the subject `LaiaGit security`.

Please include in your report:

- A description of the issue and its potential impact.
- Steps to reproduce.
- Affected version (commit SHA or release tag).
- Any proof-of-concept code or screenshots, if applicable.

## What to expect

- We will acknowledge receipt within **3 working days**.
- We will provide an initial assessment within **7 working days**.
- We will keep you informed about the status until resolution.
- Once a fix is ready, we coordinate disclosure with you.

## Scope

In scope:

- The LaiaGit application itself (Python source under `laiagit/`).
- Configuration handling (anything reading or writing `~/.laiagit/config.yaml`).
- Pre-flight checks (secret detection rules).
- Interactions with external AI backends (Ollama, Claude Code CLI, Anthropic /
  OpenAI API).

Out of scope:

- Vulnerabilities in third-party dependencies (please report those upstream).
- Issues that require physical access to a user's machine.
- Social engineering attacks.

## Hall of Fame

We will publicly acknowledge security researchers who responsibly disclose
issues here once we have shipped fixes.
