.PHONY: run test

run:
	.venv/bin/stock-reviewer

test:
	.venv/bin/python -m pytest
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/mypy	
