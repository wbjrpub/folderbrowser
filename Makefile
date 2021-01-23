# https://python-poetry.org/

all: format lint test

build:
	@rm -rf dist
	@poetry build

clean:
	@rm -rf .pytest-incremental

format:
	@poetry run black .

lint:
	@poetry run pylint ./folderbrowser
	@poetry run black --check .

publish:
	@poetry run twine upload --skip-existing dist/*

test:
	@poetry run pytest

test-with-coverage:
	@poetry run pytest --cov=./folderbrowser

watch:
	@poetry run ptw

.PHONY: all build clean docs format lint publish test test-with-coverage watch
