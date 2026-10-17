.DEFAULT_GOAL := help
.PHONY: help install upgrade fix lint test check build run clean

ifeq ($(shell command -v uv),)
$(error uv is not installed, see https://docs.astral.sh/uv/getting-started/installation/)
endif

help: ## Show this help
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

install: ## Install the dependencies from the lockfile
	uv sync --locked

upgrade: ## Upgrade the dependencies to their latest allowed versions
	uv lock --upgrade
	uv sync

fix: ## Apply the type fixes, format the code, then apply the lint fixes
	uv run ty check --fix
	uv run ruff format .
	uv run ruff check --fix .

lint: ## Check the lockfile, formatting, lint and types without changing anything
	uv lock --check
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check

test: ## Run the tests
	uv run pytest

check: lint test ## Everything CI checks

build: clean ## Build the wheel and the sdist into dist/
	uv build

run: ## Launch the app with the variables from .env
	uv run --env-file .env recto

clean: ## Remove build outputs and caches
	rm -rf dist .pytest_cache .ruff_cache
