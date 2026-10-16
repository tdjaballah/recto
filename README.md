# recto

A terminal app to learn things by heart with flashcards.

## Install

```bash
uv tool install git+https://github.com/tdjaballah/recto
```

Each tagged version also has its wheel attached to a [GitHub release](https://github.com/tdjaballah/recto/releases).

## Use

```bash
recto
```

Press `q` to quit.

## Develop

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

The interface is built with [Textual](https://textual.textualize.io). Tests drive the real app headless with `app.run_test()` and press keys through its `Pilot`.

## Release

Every push builds the wheel in CI. Pushing a tag publishes it as a GitHub release:

```bash
git tag v0.1.0
git push origin v0.1.0
```
