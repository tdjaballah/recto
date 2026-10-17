# recto

A terminal app, in the spirit of Anki, to learn things by heart with flashcards.

A deck holds only question/answer pairs. When it is imported, a model writes variants of every card: the question asked the other way round when that makes sense, and a few rephrasings. Each review asks one variant at random, so you learn the knowledge, not one wording. You type the answer, the model scores it and says what was missing, and [FSRS](https://github.com/open-spaced-repetition/py-fsrs) decides when the card comes back.

## Install

```bash
uv tool install recto
```

Each tagged version is published on [PyPI](https://pypi.org/project/recto/) and has its wheel attached to a [GitHub release](https://github.com/tdjaballah/recto/releases).

## Use

```bash
export OPENAI_API_KEY=...
recto
```

Press `i` to import a deck: one of the four examples (Anglais, Géographie, Vins, Maths, 50 cards each) or your own TOML file. Then pick a deck and press enter to review, or `c` to browse its cards: pick one to see its variants, where you can add, edit, delete or generate more.

| Variable | Default | |
|---|---|---|
| `OPENAI_API_KEY` | | Required: recto won't start without it |
| `RECTO_MODEL` | `gpt-5.4-mini` | Any [OpenAI model name](https://platform.openai.com/docs/models) |
| `RECTO_DB` | the user data directory | Where reviews and variants are kept |

## Write a deck

```toml
[deck]
name = "Vins"
description = "Cépages, appellations et régions viticoles françaises"
instructions = "Sois exigeant sur les appellations, tolérant sur l'orthographe des cépages."

[[cards]]
id = "chablis-cepage"
question = "Quel cépage domine les vins blancs de Chablis ?"
answer = "Chardonnay"
```

The file name is the deck id: importing `vins.toml` again updates the same deck. `instructions` is optional and is given to the model when it writes variants and grades answers. Each card needs an `id`, unique in the deck. Fixing a typo in a question keeps the card's history and regenerates its variants; changing its `id` starts it over. Cards removed from the file are removed from the deck.

## How the code is organized

```
src/recto/
  domain/      cards, variants, grades, FSRS memory, today's cards, what a re-import changes
  ports/       what the app needs from outside: a deck repository, a variant generator, an answer judge, a clock
  use_cases/   one class per action: import a deck, list decks, next card, submit an answer, manage variants
  adapters/    SQLite, PydanticAI, the TOML deck files, the system clock, an in-memory repository
  tui/         Textual screens, calling use cases only
  decks/       the four example decks
  container.py the one place where adapters are plugged into ports
```

## Develop

```bash
make install
cp .example.env .env   # then put your OpenAI key in .env, which git ignores
make run
make check
```

`make help` lists the other targets. Tests use fakes, never mocks: use cases run on an in-memory repository, a fake generator, a fake judge and a fixed clock, and the TUI tests drive the real app headless through Textual's `Pilot`. The SQLite repository is tested against a real database file.

## Release

Every push builds the wheel in CI. Pushing a tag on a commit of `main` that matches the version in `pyproject.toml` publishes it on PyPI, through [trusted publishing](https://docs.pypi.org/trusted-publishers/), and as a GitHub release:

```bash
uv version --bump minor
git commit -am "chore(release): 0.2.0"
git tag v0.2.0
git push origin main v0.2.0
```
