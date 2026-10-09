.PHONY: run test

run:
	.venv/bin/stock-reviewer

test:
	.venv/bin/python -m pytest
