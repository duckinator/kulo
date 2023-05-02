# Releasing Kulo

Kulo is built and released using [Bork](https://github.com/duckinator/bork).

## Release Process

Any time `__version__` is changed in `kulo/version.py` on the `main` branch, a new release is made.


Full release process:

1. Merge PR incrementing `__version__` in `kulo/__init__.py`.
2. Let the automated processes do everything else.
