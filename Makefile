.PHONY : docs
docs :
	rm -rf docs/build/
	sphinx-autobuild -b html --watch cycletls/ docs/source/ docs/build/

.PHONY : run-checks
run-checks :
	uv run ruff check cycletls
	uv run ruff format --check cycletls
	uv run pyright cycletls
	uv run pytest -v --color=yes tests/
