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
#	@poetry run pytest --cov=./folderbrowser

test-nocov:
	@poetry run pytest

watch:
	@poetry run ptw

.PHONY: build docs test
