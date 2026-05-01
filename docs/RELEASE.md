# Releasing LaiaGit

LaiaGit ships pre-built binaries for macOS, Windows, and Linux on every
tagged release. Tags are the trigger — pushing a tag like `v0.1.0` or
`v0.2.0-alpha` runs the release workflow, which builds the three
binaries in parallel and attaches them to a GitHub Release.

## Cutting a release

```bash
# 1. Make sure main is green and you're on it
git checkout main
git pull

# 2. Tag (use semver; suffix -alpha / -beta / -rc for pre-releases)
git tag -a v0.1.0-alpha -m "v0.1.0-alpha"

# 3. Push the tag
git push origin v0.1.0-alpha
```

That's it. GitHub Actions takes ~10–15 min to:
1. Spin up `macos-latest`, `windows-latest`, and `ubuntu-latest` runners in parallel.
2. Install Flutter 3.41.4 + Flet CLI on each.
3. Run `flet build {macos,windows,linux}`.
4. Zip / tar the output.
5. Create a GitHub Release with auto-generated notes from PRs since the previous tag.
6. Attach `LaiaGit-macos.zip`, `LaiaGit-windows.zip`, `LaiaGit-linux.tar.gz`.

Pre-releases (tags containing `-`, e.g. `v0.1.0-alpha`) are marked as
*pre-release* on GitHub so they don't show up as the "Latest release"
banner.

## Manual run

If you want to test the build pipeline without cutting a tag, go to
**Actions → Release → Run workflow**. This builds the three binaries
but does **not** create a GitHub Release — only artifacts you can
download from the run page.

## Local builds

You can build locally if you want to test the produced binary on your
own machine. Requirements:

- Flutter SDK 3.41.4 (Flet will offer to install it the first time).
- Platform-specific:
  - **macOS:** full Xcode + CocoaPods (`brew install cocoapods`).
  - **Windows:** Visual Studio with "Desktop development with C++" workload.
  - **Linux:** `ninja-build libgtk-3-dev libayatana-appindicator3-dev`.

Then:

```bash
.venv/bin/flet build macos --module-name laiagit
# or windows / linux
```

Output lands in `build/<platform>/`.

The first build takes 5–10 min while Flutter compiles deps. Subsequent
builds are 1–2 min.

## What users see

When a release is published, users go to
[Releases](https://github.com/laiadesk-app/LaiaGit/releases), pick the
asset for their OS, download, and run.

- macOS: unzip → drag `LaiaGit.app` to Applications.
- Windows: unzip → run `LaiaGit.exe`.
- Linux: untar → run the `LaiaGit` binary inside.

## Code signing (not yet)

Binaries are currently **unsigned**. Users will see:

- macOS: "LaiaGit cannot be opened because it is from an unidentified developer." → right-click the app → *Open* (then accept the warning).
- Windows: SmartScreen warning → *More info* → *Run anyway*.

Signing requires:
- macOS: Apple Developer ID (~$99/year) + notarisation.
- Windows: Code-signing certificate (~$200–$500/year).

If/when we sign, the workflow needs `secrets.MACOS_CERT_P12`,
`secrets.MACOS_CERT_PASSWORD`, `secrets.WINDOWS_CERT_PFX`, etc., and
the `flet build` flags `--ios-signing-certificate` / equivalent.

## Tracking downloads

GitHub gives per-asset download counters automatically. From the CLI:

```bash
gh api repos/laiadesk-app/LaiaGit/releases \
  --jq '.[] | {tag: .tag_name, assets: [.assets[] | {name, downloads: .download_count}]}'
```

See `docs/STATISTICS.md` for the full set of metrics GitHub exposes
(traffic, clones, stars, forks, downloads) and what is **not**
exposed (per-user identity).
