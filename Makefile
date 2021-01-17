all: lint test

build:
	@rm -rf dist
	@poetry build

clean:
	@rm -rf .pytest-incremental

format:
	@poetry run black .

lint:
	@poetry run pylint ./folderserver
	@poetry run black --check .

publish:
	@poetry run twine upload --skip-existing dist/*

test:
	@poetry run pytest --cov=./folderserver

test-nocov:
	@poetry run pytest

watch:
	@poetry run ptw

.PHONY: build docs test
