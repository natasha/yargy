
test:
	flake8 yargy tests
	pytest -vv --doctest-modules yargy tests

exec-docs:
	jupyter nbconvert \
		--ClearMetadataPreprocessor.enabled=True \
		--execute --to notebook --inplace \
		docs/*.ipynb

clean:
	find . \
		-name '*.pyc' \
		-o -name __pycache__ \
		-o -name .ipynb_checkpoints \
		-o -name .DS_Store \
		| xargs rm -rf

	rm -rf dist/ build/ .pytest_cache/ .cache/ *.egg-info/
