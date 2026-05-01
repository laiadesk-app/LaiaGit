"""Top-level entry point for `flet build` / `flet run`.

`flet build` requires a single `main.py` (or whatever module-name is
configured) at the project root that exposes a `main(page)` callable
Flet can hand a `ft.Page` to. Our actual app code lives inside the
`laiagit` package — this file just re-exports `main` so the Flet
toolchain can find it.
"""

from laiagit.app import main  # noqa: F401  (re-exported for flet build)

if __name__ == "__main__":
    from laiagit.app import run

    run()
