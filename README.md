# frigo

A command-line tool that keeps track of what is in my fridge and asks a language model what to cook with it.

The model is never trusted: a recipe that uses ingredients I don't have, or ignores what is about to expire, is rejected and asked again once.

## Install

```bash
uv tool install git+https://github.com/tdjaballah/frigo
```

## Use

```bash
frigo add eggs --qty 6 --expires 2026-10-20
frigo add cream --expires 2026-10-15
frigo add rice
frigo list
frigo cook --servings 2 --missing 1
frigo remove rice
```

`--missing` is the number of ingredients I accept to buy. Salt, pepper, water and oil are assumed to be there. Expired ingredients are thrown away the next time the fridge is read.

The fridge lives in `~/.frigo.db` (override with `FRIGO_DB`).

## Choose the chef

By default the chef is a model running on your machine with [Ollama](https://ollama.com). Nothing leaves your computer and no account is needed:

```bash
ollama serve
ollama pull qwen2.5:1.5b
```

Or, with Docker:

```bash
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama alpine/ollama
docker exec ollama ollama pull qwen2.5:1.5b
```

To let OpenAI cook instead:

```bash
export FRIGO_CHEF=openai
export OPENAI_API_KEY=...
```

| Variable | Default | |
|---|---|---|
| `FRIGO_CHEF` | `ollama` | `ollama` or `openai` |
| `FRIGO_OLLAMA_URL` | `http://localhost:11434` | Where Ollama listens |
| `FRIGO_OLLAMA_MODEL` | `qwen2.5:1.5b` | Any model pulled in Ollama |
| `FRIGO_OPENAI_MODEL` | `gpt-5.4-mini` | Any OpenAI model with structured outputs |

## How the code is organized

```
src/frigo/
  domain/      rules: ingredients, expiry, what makes a recipe acceptable
  ports/       what the app needs from outside: a pantry, a chef, a clock
  use_cases/   one class per action: add, remove, list, suggest a recipe
  adapters/    SQLite, the Ollama and OpenAI chefs, the system clock, an in-memory pantry
  cli/         Typer commands: parse, call a use case, print
  container.py the one place where adapters are plugged into ports
```

Dependencies point inward. The domain imports nothing from the other layers, and the use cases only know the ports, so the rules are tested without a database, a network or an API key.

## Develop

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

Each layer gets the cheapest test that gives real confidence:

| Layer | Test | Uses |
|---|---|---|
| Domain | Unit | Nothing, the rules are pure functions |
| Use cases | Unit | The production container with fakes plugged in (`tests/container.py`) |
| CLI | Contract | Stubbed use cases: only parsing, output and exit codes are checked |
| Adapters | Integration | A temporary SQLite file, and a real model in Docker for the chefs |

The SQLite and in-memory pantries share one contract test module, so the fake used everywhere else behaves like the real one.

The two chefs share one contract test module too. It runs against a small model served by Ollama, started with [Testcontainers](https://testcontainers.com): the Ollama chef through Ollama's own API, the OpenAI chef through its OpenAI-compatible one. These are the only tests that need Docker, and the only slow ones. To skip them:

```bash
uv run pytest -m "not container"
```
