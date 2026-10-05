.PHONY: repl server test coverage

repl:
	python -m src.repl

server:
	python -m src.server

test:
	pytest -v

coverage:
	coverage run --branch -m pytest
	coverage report -m